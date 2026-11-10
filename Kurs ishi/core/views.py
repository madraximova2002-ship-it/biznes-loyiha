import json
from datetime import timedelta, date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, F, Count, Avg, Q
from django.utils import timezone
from django.core.paginator import Paginator

from core.models import (
    UserProfile, Warehouse, Category, Supplier, Product,
    InventoryTransaction, WarehouseStock, AnalyticsResult,
    Forecast, AuditLog
)
from core.forms import (
    LoginForm, WarehouseForm, CategoryForm, SupplierForm,
    ProductForm, TransactionForm
)
from core.services.analytics import AnalyticsService
from core.services.optimization import OptimizationService
from core.services.forecast import ForecastService


def log_action(request, action, model_name='', object_id=None, details=None):
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        model_name=model_name,
        object_id=object_id,
        details=details or {},
        ip_address=request.META.get('REMOTE_ADDR'),
    )


# ─── AUTH ───
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_action(request, 'Tizimga kirdi', 'User', user.id)
            return redirect('dashboard')
        else:
            messages.error(request, "Foydalanuvchi nomi yoki parol noto'g'ri!")
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


def toggle_view(request):
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            profile.dark_mode = not profile.dark_mode
            profile.save()
            return JsonResponse({'status': 'ok', 'dark_mode': profile.dark_mode})
        except UserProfile.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

def logout_view(request):
    if request.user.is_authenticated:
        log_action(request, 'Tizimdan chiqdi', 'User', request.user.id)
    logout(request)
    return redirect('login')


# ─── ROLE CHECK ───
def has_role(user, roles):
    if user.is_superuser:
        return True
    try:
        return user.profile.role in roles
    except UserProfile.DoesNotExist:
        return False


def safe_int(value, default=None):
    """Query parametrni xavfsiz int ga o'tkazish"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# ─── DASHBOARD ───
@login_required
def dashboard(request):
    warehouses = Warehouse.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # Umumiy statistika
    total_products = products.count()
    total_warehouses = warehouses.count()
    total_suppliers = Supplier.objects.filter(is_active=True).count()

    # Umumiy ombor qiymati
    total_value = WarehouseStock.objects.aggregate(
        total=Sum(F('quantity') * F('product__price'))
    )['total'] or 0

    # Bugungi tranzaksiyalar
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_transactions = InventoryTransaction.objects.filter(created_at__gte=today_start).count()

    # Minimal zaxiradan past
    low_stock_products = list(WarehouseStock.objects.select_related('product', 'warehouse').filter(
        quantity__gt=0,
        quantity__lt=F('product__min_stock')
    ))

    # Sekin aylanuvchi mollar (60 kun)
    sixty_days_ago = now - timedelta(days=60)
    in_stock_products = WarehouseStock.objects.values('product_id').annotate(
        t=Sum('quantity')
    ).filter(t__gt=0).values_list('product_id', flat=True)
    recent_sold_products = InventoryTransaction.objects.filter(
        transaction_type='out', created_at__gte=sixty_days_ago
    ).values_list('product_id', flat=True).distinct()
    
    slow_count = products.filter(id__in=in_stock_products).exclude(id__in=recent_sold_products).count()

    # Oxirgi 30 kunlik kirim-chiqim
    daily_data = []
    for d in range(30):
        day = now - timedelta(days=29 - d)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        in_qty = InventoryTransaction.objects.filter(
            transaction_type='in', created_at__gte=day_start, created_at__lt=day_end
        ).aggregate(total=Sum('quantity'))['total'] or 0
        out_qty = InventoryTransaction.objects.filter(
            transaction_type='out', created_at__gte=day_start, created_at__lt=day_end
        ).aggregate(total=Sum('quantity'))['total'] or 0
        daily_data.append({
            'date': day.strftime('%d.%m'),
            'in': int(in_qty),
            'out': int(out_qty),
        })

    # Eng ko'p sotilgan top 10
    top_products = InventoryTransaction.objects.filter(
        transaction_type='out', created_at__gte=thirty_days_ago
    ).values('product__name').annotate(
        total=Sum('quantity')
    ).order_by('-total')[:10]

    # Filiallar bo'yicha qiymat
    warehouse_values = []
    for wh in warehouses:
        val = WarehouseStock.objects.filter(warehouse=wh).aggregate(
            total=Sum(F('quantity') * F('product__price'))
        )['total'] or 0
        warehouse_values.append({'name': wh.name, 'value': float(val)})

    # Oxirgi tranzaksiyalar
    recent_transactions = InventoryTransaction.objects.select_related(
        'product', 'warehouse', 'created_by'
    ).order_by('-created_at')[:10]

    # Yaroqlilik muddati tugayotgan mahsulotlar (30 kun ichida)
    expiring_threshold = now.date() + timedelta(days=30)
    expiring_products = list(Product.objects.filter(
        is_active=True, 
        expire_date__isnull=False, 
        expire_date__lte=expiring_threshold
    ).order_by('expire_date'))

    context = {
        'total_products': total_products,
        'total_warehouses': total_warehouses,
        'total_suppliers': total_suppliers,
        'total_value': total_value,
        'today_transactions': today_transactions,
        'low_stock_products': low_stock_products,
        'low_stock_count': len(low_stock_products),
        'slow_count': slow_count,
        'expiring_products': expiring_products,
        'expiring_count': len(expiring_products),
        'daily_data_json': json.dumps(daily_data),
        'top_products_json': json.dumps(list(top_products)),
        'warehouse_values_json': json.dumps(warehouse_values),
        'recent_transactions': recent_transactions,
        'page_title': 'Boshqaruv paneli',
    }
    return render(request, 'core/dashboard.html', context)


# ─── WAREHOUSES ───
@login_required
def warehouse_list(request):
    warehouses = Warehouse.objects.all()
    for wh in warehouses:
        wh.total_val = wh.total_value()
        wh.product_count = WarehouseStock.objects.filter(warehouse=wh, quantity__gt=0).count()
    return render(request, 'core/warehouse_list.html', {
        'warehouses': warehouses,
        'page_title': 'Omborlar'
    })


@login_required
def warehouse_create(request):
    if not has_role(request.user, ['admin', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('warehouse_list')
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            wh = form.save()
            log_action(request, 'Ombor yaratildi', 'Warehouse', wh.id, {'name': wh.name})
            messages.success(request, f"'{wh.name}' ombori yaratildi!")
            return redirect('warehouse_list')
    else:
        form = WarehouseForm()
    return render(request, 'core/warehouse_form.html', {'form': form, 'page_title': "Yangi ombor"})


@login_required
def warehouse_edit(request, pk):
    if not has_role(request.user, ['admin', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('warehouse_list')
    wh = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=wh)
        if form.is_valid():
            form.save()
            log_action(request, 'Ombor tahrirlandi', 'Warehouse', wh.id)
            messages.success(request, "Ombor yangilandi!")
            return redirect('warehouse_list')
    else:
        form = WarehouseForm(instance=wh)
    return render(request, 'core/warehouse_form.html', {'form': form, 'page_title': "Omborni tahrirlash"})


@login_required
def warehouse_delete(request, pk):
    if not has_role(request.user, ['admin']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('warehouse_list')
    wh = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        log_action(request, 'Ombor o\'chirildi', 'Warehouse', wh.id, {'name': wh.name})
        wh.delete()
        messages.success(request, "Ombor o'chirildi!")
    return redirect('warehouse_list')


# ─── PRODUCTS ───
@login_required
def product_list(request):
    products = Product.objects.select_related('category', 'supplier').all()
    q = request.GET.get('q', '')
    cat = request.GET.get('category', '')
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    if cat:
        products = products.filter(category_id=cat)

    paginator = Paginator(products, 20)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)
    
    # Calculate stock only for current page items
    for p in products_page:
        p.total_stock = WarehouseStock.objects.filter(product=p).aggregate(t=Sum('quantity'))['t'] or 0
        p.stock_status = 'danger' if p.total_stock < p.min_stock else ('warning' if p.total_stock < p.min_stock * 2 else 'success')

    categories = Category.objects.all()

    return render(request, 'core/product_list.html', {
        'products': products_page,
        'categories': categories,
        'q': q,
        'selected_category': cat,
        'selected_category_id': safe_int(cat),
        'page_title': 'Mahsulotlar'
    })


@login_required
def product_import_excel(request):
    if not has_role(request.user, ['admin', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('product_list')
        
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        if not excel_file.name.endswith('.xlsx'):
            messages.error(request, 'Faqat .xlsx fayl formatiga ruxsat beriladi')
            return redirect('product_list')
            
        try:
            import openpyxl
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
            
            created_count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):  # Skip header
                if not row[0]: # SKU bo'sh bo'lsa o'tkazib yuborish
                    continue
                    
                sku = str(row[0])
                name = str(row[1]) if row[1] else 'Nomsiz'
                price = Decimal(str(row[2])) if row[2] else Decimal('0')
                cost_price = Decimal(str(row[3])) if row[3] else Decimal('0')
                min_stock = Decimal(str(row[4])) if row[4] else Decimal('0')
                
                # Create or update product
                p, created = Product.objects.update_or_create(
                    sku=sku,
                    defaults={
                        'name': name,
                        'price': price,
                        'cost_price': cost_price,
                        'min_stock': min_stock,
                    }
                )
                if created:
                    created_count += 1
                    
            log_action(request, f'Excel orqali {created_count} ta mahsulot import qilindi', 'Product', None)
            messages.success(request, f"Muvaffaqiyatli import qilindi: {created_count} ta yangi mahsulot қўshildi yoki yangilandi!")
        except Exception as e:
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
            
    return redirect('product_list')


@login_required
def product_create(request):
    if not has_role(request.user, ['admin', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('product_list')
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            p = form.save()
            log_action(request, 'Mahsulot yaratildi', 'Product', p.id, {'name': p.name})
            messages.success(request, f"'{p.name}' mahsuloti yaratildi!")
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'core/product_form.html', {'form': form, 'page_title': "Yangi mahsulot"})


@login_required
def product_edit(request, pk):
    if not has_role(request.user, ['admin', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('product_list')
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            log_action(request, 'Mahsulot tahrirlandi', 'Product', product.id)
            messages.success(request, "Mahsulot yangilandi!")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'core/product_form.html', {'form': form, 'page_title': "Mahsulotni tahrirlash"})


@login_required
def product_delete(request, pk):
    if not has_role(request.user, ['admin']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('product_list')
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        log_action(request, "Mahsulot o'chirildi", 'Product', product.id, {'name': product.name})
        product.delete()
        messages.success(request, "Mahsulot o'chirildi!")
    return redirect('product_list')


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    stocks = WarehouseStock.objects.filter(product=product).select_related('warehouse')
    total_stock = stocks.aggregate(t=Sum('quantity'))['t'] or 0
    transactions = InventoryTransaction.objects.filter(product=product).select_related(
        'warehouse', 'target_warehouse', 'created_by'
    ).order_by('-created_at')[:20]

    # Optimallashtirish
    optimization = OptimizationService.get_product_recommendations(product)

    return render(request, 'core/product_detail.html', {
        'product': product,
        'stocks': stocks,
        'total_stock': total_stock,
        'transactions': transactions,
        'optimization': optimization,
        'page_title': product.name,
    })


# ─── SUPPLIERS ───
@login_required
def supplier_list(request):
    suppliers = Supplier.objects.annotate(product_count=Count('products'))
    return render(request, 'core/supplier_list.html', {
        'suppliers': suppliers,
        'page_title': 'Yetkazib beruvchilar'
    })


@login_required
def supplier_create(request):
    if not has_role(request.user, ['admin', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('supplier_list')
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            s = form.save()
            log_action(request, 'Yetkazib beruvchi yaratildi', 'Supplier', s.id)
            messages.success(request, f"'{s.name}' yaratildi!")
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'core/supplier_form.html', {'form': form, 'page_title': "Yangi yetkazib beruvchi"})


@login_required
def supplier_edit(request, pk):
    if not has_role(request.user, ['admin', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('supplier_list')
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            log_action(request, 'Yetkazib beruvchi tahrirlandi', 'Supplier', supplier.id)
            messages.success(request, "Yangilandi!")
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'core/supplier_form.html', {'form': form, 'page_title': "Yetkazib beruvchini tahrirlash"})


@login_required
def supplier_delete(request, pk):
    if not has_role(request.user, ['admin']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('supplier_list')
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        log_action(request, "Yetkazib beruvchi o'chirildi", 'Supplier', supplier.id)
        supplier.delete()
        messages.success(request, "O'chirildi!")
    return redirect('supplier_list')


# ─── CATEGORIES ───
@login_required
def category_list(request):
    categories = Category.objects.annotate(product_count=Count('products'))
    return render(request, 'core/category_list.html', {
        'categories': categories,
        'page_title': 'Kategoriyalar'
    })


@login_required
def category_create(request):
    if not has_role(request.user, ['admin', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('category_list')
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            c = form.save()
            log_action(request, 'Kategoriya yaratildi', 'Category', c.id, {'name': c.name})
            messages.success(request, f"'{c.name}' kategoriyasi yaratildi!")
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'core/category_form.html', {'form': form, 'page_title': "Yangi kategoriya"})


@login_required
def category_edit(request, pk):
    if not has_role(request.user, ['admin', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('category_list')
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            log_action(request, 'Kategoriya tahrirlandi', 'Category', cat.id)
            messages.success(request, "Kategoriya yangilandi!")
            return redirect('category_list')
    else:
        form = CategoryForm(instance=cat)
    return render(request, 'core/category_form.html', {'form': form, 'page_title': "Kategoriyani tahrirlash"})


@login_required
def category_delete(request, pk):
    if not has_role(request.user, ['admin']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('category_list')
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        log_action(request, "Kategoriya o'chirildi", 'Category', cat.id, {'name': cat.name})
        cat.delete()
        messages.success(request, "Kategoriya o'chirildi!")
    return redirect('category_list')


# ─── TRANSACTIONS ───
@login_required
def transaction_list(request):
    transactions = InventoryTransaction.objects.select_related(
        'product', 'warehouse', 'target_warehouse', 'created_by'
    ).all()
    t_type = request.GET.get('type', '')
    wh = request.GET.get('warehouse', '')
    if t_type:
        transactions = transactions.filter(transaction_type=t_type)
    if wh:
        transactions = transactions.filter(warehouse_id=wh)

    paginator = Paginator(transactions, 25)
    page = request.GET.get('page')
    transactions = paginator.get_page(page)
    warehouses = Warehouse.objects.filter(is_active=True)

    return render(request, 'core/transaction_list.html', {
        'transactions': transactions,
        'warehouses': warehouses,
        'selected_type': t_type,
        'selected_warehouse': wh,
        'selected_warehouse_id': safe_int(wh),
        'page_title': 'Kirim-Chiqim'
    })


@login_required
def transaction_create(request):
    if not has_role(request.user, ['admin', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('transaction_list')
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.created_by = request.user
            txn.save()
            log_action(request, f'{txn.get_transaction_type_display()} amalga oshirildi',
                        'InventoryTransaction', txn.id,
                        {'product': txn.product.name, 'quantity': txn.quantity})
            messages.success(request, f"{txn.get_transaction_type_display()} muvaffaqiyatli amalga oshirildi!")
            return redirect('transaction_list')
    else:
        form = TransactionForm()
    return render(request, 'core/transaction_form.html', {'form': form, 'page_title': "Yangi tranzaksiya"})


@login_required
def transaction_invoice(request, pk):
    txn = get_object_or_404(InventoryTransaction, pk=pk)
    return render(request, 'core/transaction_invoice.html', {
        'txn': txn,
        'page_title': f"Chek #{txn.id}"
    })


# ─── ANALYTICS ───
@login_required
def analytics_view(request):
    if not has_role(request.user, ['admin', 'analyst', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('dashboard')

    warehouse_id = request.GET.get('warehouse')
    warehouse = None
    if warehouse_id:
        warehouse = Warehouse.objects.filter(id=warehouse_id).first()

    abc_results = AnalyticsService.abc_analysis(warehouse)
    xyz_results = AnalyticsService.xyz_analysis(warehouse)
    turnover_results = AnalyticsService.inventory_turnover(warehouse)
    slow_results = AnalyticsService.slow_moving_products(warehouse)
    frozen = AnalyticsService.frozen_capital(warehouse)

    warehouses = Warehouse.objects.filter(is_active=True)

    # Prepare chart data
    abc_chart = {'A': 0, 'B': 0, 'C': 0}
    for item in abc_results:
        abc_chart[item['category']] += 1

    xyz_chart = {'X': 0, 'Y': 0, 'Z': 0}
    for item in xyz_results:
        xyz_chart[item['category']] += 1

    # Enrich results with product names
    product_ids = [r['product_id'] for r in abc_results]
    products_map = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
    for r in abc_results:
        r['product'] = products_map.get(r['product_id'])

    context = {
        'abc_results': abc_results,
        'xyz_results': xyz_results,
        'turnover_results': turnover_results[:20],
        'slow_results': slow_results,
        'frozen': frozen,
        'warehouses': warehouses,
        'selected_warehouse': warehouse_id or '',
        'selected_warehouse_id': safe_int(warehouse_id),
        'abc_chart_json': json.dumps(abc_chart),
        'xyz_chart_json': json.dumps(xyz_chart),
        'page_title': 'Analitika',
    }
    return render(request, 'core/analytics.html', context)


# ─── OPTIMIZATION ───
@login_required
def optimization_view(request):
    if not has_role(request.user, ['admin', 'analyst', 'manager']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('dashboard')

    products = Product.objects.filter(is_active=True)
    recommendations = []
    for product in products:
        try:
            rec = OptimizationService.get_product_recommendations(product)
            recommendations.append(rec)
        except Exception:
            pass

    # Only products needing reorder
    needs_reorder = [r for r in recommendations if r['needs_reorder']]

    context = {
        'recommendations': recommendations,
        'needs_reorder': needs_reorder,
        'page_title': 'Optimallashtirish',
    }
    return render(request, 'core/optimization.html', context)


# ─── FORECAST ───
@login_required
def forecast_view(request):
    if not has_role(request.user, ['admin', 'analyst']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('dashboard')

    product_id = request.GET.get('product')
    forecast_data = None
    selected_product = None

    if product_id:
        selected_product = Product.objects.filter(id=product_id).first()
        if selected_product:
            forecast_data = ForecastService.generate_full_forecast(selected_product)

    products = Product.objects.filter(is_active=True)

    context = {
        'products': products,
        'selected_product': selected_product,
        'forecast_data': forecast_data,
        'page_title': 'Prognoz',
    }

    # Prepare chart data if forecast exists
    if forecast_data:
        ma7_chart = []
        for p in forecast_data.get('ma_7', {}).get('predictions', []):
            ma7_chart.append({'date': p['date'].strftime('%d.%m'), 'value': p['predicted']})
        es7_chart = []
        for p in forecast_data.get('es_7', {}).get('predictions', []):
            es7_chart.append({'date': p['date'].strftime('%d.%m'), 'value': p['predicted']})
        context['ma7_chart_json'] = json.dumps(ma7_chart)
        context['es7_chart_json'] = json.dumps(es7_chart)

    return render(request, 'core/forecast.html', context)


# ─── REPORTS ───
@login_required
def reports_view(request):
    warehouses = Warehouse.objects.filter(is_active=True)
    context = {
        'warehouses': warehouses,
        'page_title': 'Hisobotlar',
    }
    return render(request, 'core/reports.html', context)


@login_required
def report_daily(request):
    """Kunlik hisobot"""
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    transactions = InventoryTransaction.objects.filter(
        created_at__gte=today, created_at__lt=tomorrow
    ).select_related('product', 'warehouse', 'created_by')

    in_total = transactions.filter(transaction_type='in').aggregate(
        qty=Sum('quantity'), val=Sum('total_price')
    )
    out_total = transactions.filter(transaction_type='out').aggregate(
        qty=Sum('quantity'), val=Sum('total_price')
    )

    context = {
        'transactions': transactions,
        'in_total': in_total,
        'out_total': out_total,
        'report_date': today,
        'page_title': 'Kunlik hisobot',
    }
    return render(request, 'core/report_daily.html', context)


@login_required
def export_excel(request):
    """Excel eksport"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    report_type = request.GET.get('type', 'products')
    wb = openpyxl.Workbook()
    ws = wb.active

    header_font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1a73e8', end_color='1a73e8', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    if report_type == 'products':
        ws.title = "Mahsulotlar"
        headers = ['SKU', 'Nomi', 'Kategoriya', 'Narxi', 'Zaxira', 'Min zaxira', 'Holat']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border

        for row, product in enumerate(Product.objects.select_related('category').filter(is_active=True), 2):
            total_stock = WarehouseStock.objects.filter(product=product).aggregate(t=Sum('quantity'))['t'] or 0
            status = 'Xavfli' if total_stock < product.min_stock else 'Normal'
            data = [product.sku, product.name, str(product.category or ''), float(product.price),
                    total_stock, product.min_stock, status]
            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = thin_border

    elif report_type == 'transactions':
        ws.title = "Tranzaksiyalar"
        headers = ['Sana', 'Turi', 'Mahsulot', 'Ombor', 'Miqdor', 'Narx', 'Jami']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border

        txns = InventoryTransaction.objects.select_related('product', 'warehouse').all()[:500]
        for row, txn in enumerate(txns, 2):
            data = [
                txn.created_at.strftime('%d.%m.%Y %H:%M'),
                txn.get_transaction_type_display(),
                txn.product.name,
                txn.warehouse.name,
                txn.quantity,
                float(txn.unit_price),
                float(txn.total_price),
            ]
            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = thin_border

    # Auto-width
    for col in ws.columns:
        max_length = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 4, 40)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="hisobot_{report_type}.xlsx"'
    wb.save(response)
    return response


@login_required
def export_pdf(request):
    """PDF eksport"""
    from xhtml2pdf import pisa
    from io import BytesIO

    report_type = request.GET.get('type', 'products')

    if report_type == 'products':
        products = Product.objects.select_related('category').filter(is_active=True)
        for p in products:
            p.total_stock = WarehouseStock.objects.filter(product=p).aggregate(t=Sum('quantity'))['t'] or 0

        html = render(request, 'core/pdf_products.html', {'products': products}).content.decode('utf-8')
    else:
        transactions = InventoryTransaction.objects.select_related('product', 'warehouse').all()[:200]
        html = render(request, 'core/pdf_transactions.html', {'transactions': transactions}).content.decode('utf-8')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="hisobot_{report_type}.pdf"'

    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    response.write(buffer.getvalue())
    buffer.close()
    return response


# ─── AUDIT LOG ───
@login_required
def audit_log_view(request):
    if not has_role(request.user, ['admin']):
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('dashboard')

    logs = AuditLog.objects.select_related('user').all()
    paginator = Paginator(logs, 30)
    page = request.GET.get('page')
    logs = paginator.get_page(page)

    return render(request, 'core/audit_log.html', {
        'logs': logs,
        'page_title': 'Audit log'
    })


@login_required
def api_dashboard_data(request):
    """Dashboard uchun real-time ma'lumotlar"""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    data = {
        'total_value': float(WarehouseStock.objects.aggregate(
            total=Sum(F('quantity') * F('product__price'))
        )['total'] or 0),
        'today_in': int(InventoryTransaction.objects.filter(
            transaction_type='in', created_at__gte=today_start
        ).aggregate(total=Sum('quantity'))['total'] or 0),
        'today_out': int(InventoryTransaction.objects.filter(
            transaction_type='out', created_at__gte=today_start
        ).aggregate(total=Sum('quantity'))['total'] or 0),
    }
    return JsonResponse(data)


@login_required
def api_notifications(request):
    """Burchakdagi qo'ng'iroqcha uchun Push Notifications"""
    notifications = []
    
    # 1. Past zaxira (Qizil qoldiqlar)
    low_stocks = WarehouseStock.objects.select_related('product', 'warehouse').filter(
        quantity__lt=F('product__min_stock'), quantity__gt=0
    )
    for stock in low_stocks:
        notifications.append({
            'type': 'danger',
            'title': "Zaxira tugamoqda",
            'message': f"{stock.product.name} ({stock.warehouse.name}da {stock.quantity} qoldi)",
            'url': f"/products/{stock.product.id}/"
        })
        
    # 2. Yaroqlilik muddati tugayotgan mahsulotlar (30 kun ichida)
    now = timezone.now()
    expiring_threshold = now.date() + timedelta(days=30)
    expiring_products = list(Product.objects.filter(
        is_active=True,
        expire_date__isnull=False,
        expire_date__lte=expiring_threshold
    ).order_by('expire_date'))
    for p in expiring_products:
        notifications.append({
            'type': 'warning',
            'title': "Sana o'tmoqda",
            'message': f"{p.name} yaroqlilik sanasi {p.expire_date.strftime('%d.%m.%Y')} da tugaydi",
            'url': f"/products/{p.id}/"
        })
        
    return JsonResponse({
        'count': len(notifications),
        'notifications': notifications[:10]  # Only show top 10 in dropdown
    })
