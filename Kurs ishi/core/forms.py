from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from core.models import (
    UserProfile, Warehouse, Category, Supplier, Product,
    InventoryTransaction
)


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Foydalanuvchi nomi', 'autofocus': True}),
        label='Foydalanuvchi nomi'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Parol'}),
        label='Parol'
    )


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'address', 'manager', 'phone', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ombor nomi'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Manzil'}),
            'manager': forms.Select(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+998 XX XXX XX XX'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Kategoriya nomi'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Yetkazib beruvchi nomi'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Aloqa shaxsi'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+998 XX XXX XX XX'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@example.com'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'sku', 'name', 'category', 'supplier', 'price', 'cost_price',
            'holding_cost', 'ordering_cost', 'lead_time_days', 'min_stock',
            'unit', 'expire_date', 'description', 'is_active'
        ]
        widgets = {
            'sku': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'SKU-001'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Mahsulot nomi'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'supplier': forms.Select(attrs={'class': 'form-input'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00'}),
            'holding_cost': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00'}),
            'ordering_cost': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '7'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '10'}),
            'unit': forms.TextInput(attrs={'class': 'form-input', 'placeholder': "dona"}),
            'expire_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = InventoryTransaction
        fields = ['transaction_type', 'product', 'warehouse', 'target_warehouse', 'quantity', 'unit_price', 'note']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-input', 'id': 'id_transaction_type'}),
            'product': forms.Select(attrs={'class': 'form-input'}),
            'warehouse': forms.Select(attrs={'class': 'form-input'}),
            'target_warehouse': forms.Select(attrs={'class': 'form-input'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Miqdor', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Birlik narxi'}),
            'note': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Izoh...'}),
        }
        labels = {
            'transaction_type': 'Tranzaksiya turi',
            'product': 'Mahsulot',
            'warehouse': 'Ombor',
            'target_warehouse': 'Manzil ombor (Transfer uchun)',
            'quantity': 'Miqdor',
            'unit_price': 'Birlik narxi',
            'note': 'Izoh',
        }

    def clean(self):
        cleaned_data = super().clean()
        t_type = cleaned_data.get('transaction_type')
        quantity = cleaned_data.get('quantity')
        warehouse = cleaned_data.get('warehouse')
        target_warehouse = cleaned_data.get('target_warehouse')
        product = cleaned_data.get('product')
        unit_price = cleaned_data.get('unit_price')

        if quantity is not None and quantity <= 0:
            self.add_error('quantity', "Miqdor 0 dan katta bo'lishi kerak.")

        if unit_price is not None and unit_price < 0:
            self.add_error('unit_price', "Narx manfiy bo'lishi mumkin emas.")

        if t_type == 'transfer':
            if not target_warehouse:
                self.add_error('target_warehouse', "Transfer uchun manzil ombor tanlanishi shart.")
            elif warehouse == target_warehouse:
                self.add_error('target_warehouse', "Bir xil omborga transfer qilish mumkin emas.")

        if t_type in ['out', 'transfer'] and product and warehouse and quantity:
            from django.db.models import Sum
            from core.models import WarehouseStock
            stock_qty = WarehouseStock.objects.filter(warehouse=warehouse, product=product).aggregate(t=Sum('quantity'))['t'] or 0
            if stock_qty < quantity:
                self.add_error('quantity', f"Omborda yetarli mahsulot yo'q. Haqiqiy qoldiq: {stock_qty}")

        return cleaned_data
