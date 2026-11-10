"""
Analitika xizmatlari: ABC, XYZ, Aylanish tezligi, Sekin aylanuvchi, Muzlagan kapital
"""
import numpy as np
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, F, Avg, Count
from core.models import Product, InventoryTransaction, WarehouseStock, AnalyticsResult


class AnalyticsService:

    @staticmethod
    def abc_analysis(warehouse=None, days=180):
        """ABC tahlil: mahsulotlarni daromad ulushi bo'yicha A, B, C guruhlarga ajratish"""
        since = timezone.now() - timedelta(days=days)
        txns = InventoryTransaction.objects.filter(
            transaction_type='out', created_at__gte=since
        )
        if warehouse:
            txns = txns.filter(warehouse=warehouse)

        product_revenue = txns.values('product').annotate(
            total_revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-total_revenue')

        total_revenue = float(sum(item['total_revenue'] or 0 for item in product_revenue))
        results = []
        cumulative = 0

        for item in product_revenue:
            revenue = float(item['total_revenue'] or 0)
            cumulative += revenue
            pct = (cumulative / total_revenue * 100) if total_revenue > 0 else 0

            if pct <= 80:
                category = 'A'
            elif pct <= 95:
                category = 'B'
            else:
                category = 'C'

            results.append({
                'product_id': item['product'],
                'revenue': revenue,
                'cumulative_pct': round(pct, 2),
                'category': category,
            })

            AnalyticsResult.objects.update_or_create(
                analysis_type='abc',
                product_id=item['product'],
                warehouse_id=warehouse.id if warehouse else None,
                defaults={
                    'category_label': category,
                    'value': revenue,
                    'extra_data': {'cumulative_pct': round(pct, 2)},
                }
            )
        return results

    @staticmethod
    def xyz_analysis(warehouse=None, days=180):
        """XYZ tahlil: talab barqarorligi asosida segmentatsiya"""
        since = timezone.now() - timedelta(days=days)
        products = Product.objects.filter(is_active=True)

        results = []
        for product in products:
            txns = InventoryTransaction.objects.filter(
                product=product, transaction_type='out', created_at__gte=since
            )
            if warehouse:
                txns = txns.filter(warehouse=warehouse)

            monthly_data = []
            for m in range(6):
                start = since + timedelta(days=30 * m)
                end = start + timedelta(days=30)
                qty = txns.filter(created_at__gte=start, created_at__lt=end).aggregate(
                    total=Sum('quantity')
                )['total'] or 0
                monthly_data.append(float(qty))

            mean = np.mean(monthly_data) if monthly_data else 0
            std = np.std(monthly_data) if monthly_data else 0
            cv = (std / mean * 100) if mean > 0 else 999

            if cv <= 10:
                category = 'X'
            elif cv <= 25:
                category = 'Y'
            else:
                category = 'Z'

            results.append({
                'product_id': product.id,
                'product_name': product.name,
                'cv': round(cv, 2),
                'category': category,
                'monthly_data': monthly_data,
            })

            AnalyticsResult.objects.update_or_create(
                analysis_type='xyz',
                product_id=product.id,
                warehouse_id=warehouse.id if warehouse else None,
                defaults={
                    'category_label': category,
                    'value': round(cv, 4),
                    'extra_data': {'monthly_data': monthly_data},
                }
            )

        results.sort(key=lambda x: x['cv'])
        return results

    @staticmethod
    def inventory_turnover(warehouse=None, days=180):
        """Aylanish tezligi = Sotilgan tannarx / O'rtacha zaxira"""
        since = timezone.now() - timedelta(days=days)
        products = Product.objects.filter(is_active=True)
        results = []

        for product in products:
            txns = InventoryTransaction.objects.filter(
                product=product, transaction_type='out', created_at__gte=since
            )
            if warehouse:
                txns = txns.filter(warehouse=warehouse)

            cogs = float(txns.aggregate(
                total=Sum(F('quantity') * F('unit_price'))
            )['total'] or 0)

            if warehouse:
                avg_stock = WarehouseStock.objects.filter(
                    product=product, warehouse=warehouse
                ).aggregate(avg=Avg('quantity'))['avg'] or 0
            else:
                avg_stock = WarehouseStock.objects.filter(
                    product=product
                ).aggregate(avg=Avg('quantity'))['avg'] or 0

            avg_stock_value = float(avg_stock) * float(product.price)
            turnover = cogs / avg_stock_value if avg_stock_value > 0 else 0

            results.append({
                'product_id': product.id,
                'product_name': product.name,
                'cogs': cogs,
                'avg_stock_value': avg_stock_value,
                'turnover': round(turnover, 2),
            })

            AnalyticsResult.objects.update_or_create(
                analysis_type='turnover',
                product_id=product.id,
                warehouse_id=warehouse.id if warehouse else None,
                defaults={
                    'value': round(turnover, 4),
                    'extra_data': {'cogs': cogs, 'avg_stock_value': avg_stock_value},
                }
            )

        results.sort(key=lambda x: x['turnover'], reverse=True)
        return results

    @staticmethod
    def slow_moving_products(warehouse=None, days=60):
        """60 kun sotilmagan mahsulotlar"""
        since = timezone.now() - timedelta(days=days)
        products = Product.objects.filter(is_active=True)
        slow = []

        for product in products:
            txns = InventoryTransaction.objects.filter(
                product=product, transaction_type='out', created_at__gte=since
            )
            if warehouse:
                txns = txns.filter(warehouse=warehouse)

            if not txns.exists():
                stock_qty = WarehouseStock.objects.filter(product=product)
                if warehouse:
                    stock_qty = stock_qty.filter(warehouse=warehouse)
                total_qty = stock_qty.aggregate(total=Sum('quantity'))['total'] or 0

                if total_qty > 0:
                    frozen_value = float(total_qty) * float(product.price)
                    slow.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'quantity': total_qty,
                        'frozen_value': frozen_value,
                        'days_without_sale': days,
                    })

        return slow

    @staticmethod
    def frozen_capital(warehouse=None):
        """Muzlagan kapital: sekin sotilayotgan mahsulotlar qiymati"""
        slow = AnalyticsService.slow_moving_products(warehouse, days=60)
        total_frozen = sum(item['frozen_value'] for item in slow)
        return {
            'total_frozen_capital': total_frozen,
            'products': slow,
            'count': len(slow),
        }
