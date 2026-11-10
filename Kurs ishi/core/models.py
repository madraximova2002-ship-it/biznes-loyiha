from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import math


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Mudir'),
        ('analyst', 'Tahlilchi'),
        ('observer', 'Kuzatuvchi'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='observer')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    dark_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

    class Meta:
        verbose_name = "Foydalanuvchi profili"
        verbose_name_plural = "Foydalanuvchi profillari"


class Warehouse(models.Model):
    name = models.CharField(max_length=200, verbose_name="Ombor nomi")
    address = models.TextField(blank=True, verbose_name="Manzil")
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_warehouses', verbose_name="Mudiri")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def total_value(self):
        from django.db.models import Sum, F
        result = self.stocks.aggregate(
            total=Sum(F('quantity') * F('product__price'))
        )
        return result['total'] or 0

    class Meta:
        verbose_name = "Ombor"
        verbose_name_plural = "Omborlar"
        ordering = ['name']


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="Kategoriya nomi")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ['name']


class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="Yetkazib beruvchi nomi")
    contact_person = models.CharField(max_length=200, blank=True, verbose_name="Aloqa shaxsi")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Manzil")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Yetkazib beruvchi"
        verbose_name_plural = "Yetkazib beruvchilar"
        ordering = ['name']


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU")
    name = models.CharField(max_length=300, verbose_name="Nomi")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name="Kategoriya")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name="Yetkazib beruvchi")
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Narxi (so'm)")
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Tannarxi (so'm)")
    holding_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Saqlash xarajati")
    ordering_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Buyurtma xarajati")
    lead_time_days = models.IntegerField(default=7, verbose_name="Yetkazish muddati (kun)")
    min_stock = models.IntegerField(default=10, verbose_name="Minimal zaxira")
    unit = models.CharField(max_length=20, default='dona', verbose_name="O'lchov birligi")
    expire_date = models.DateField(blank=True, null=True, verbose_name="Yaroqlilik muddati")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Rasm")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sku} - {self.name}"

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]


class WarehouseStock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stocks', verbose_name="Ombor yoki Maydon")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks', verbose_name="Qurilish materiali")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Qoldiq miqdori")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Oxirgi yangilangan vaqti")

    class Meta:
        unique_together = ['warehouse', 'product']
        verbose_name = "Ombor  zaxirasi"
        verbose_name_plural = "Omborlardagi  zaxiralari"

    def __str__(self):
        return f"{self.warehouse.name} -> {self.product.name}: {self.quantity} {self.product.get_unit_display()}"


class InventoryTransaction(models.Model):
    TYPE_CHOICES = [
        ('in', 'Kirim'),
        ('out', 'Chiqim'),
        ('transfer', 'Transfer'),
    ]
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Turi")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions', verbose_name="Mahsulot")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='transactions', verbose_name="Ombor")
    target_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_transfers', verbose_name="Manzil ombor")
    quantity = models.IntegerField(verbose_name="Miqdor")
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Birlik narxi")
    total_price = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Umumiy narx")
    note = models.TextField(blank=True, verbose_name="Izoh")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Yaratuvchi")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Update stock
        stock, created = WarehouseStock.objects.get_or_create(
            warehouse=self.warehouse, product=self.product
        )
        if self.transaction_type == 'in':
            stock.quantity += self.quantity
        elif self.transaction_type == 'out':
            stock.quantity -= self.quantity
        elif self.transaction_type == 'transfer' and self.target_warehouse:
            stock.quantity -= self.quantity
            target_stock, _ = WarehouseStock.objects.get_or_create(
                warehouse=self.target_warehouse, product=self.product
            )
            target_stock.quantity += self.quantity
            target_stock.save()
        stock.save()

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} ({self.quantity})"

    class Meta:
        verbose_name = "Tranzaksiya"
        verbose_name_plural = "Tranzaksiyalar"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['product', 'created_at']),
        ]


class AnalyticsResult(models.Model):
    TYPE_CHOICES = [
        ('abc', 'ABC tahlil'),
        ('xyz', 'XYZ tahlil'),
        ('turnover', 'Aylanish tezligi'),
        ('slow_moving', 'Sekin aylanuvchi'),
        ('frozen_capital', 'Muzlagan kapital'),
    ]
    analysis_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='analytics', null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, null=True, blank=True)
    category_label = models.CharField(max_length=10, blank=True)
    value = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    extra_data = models.JSONField(default=dict, blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tahlil natijasi"
        verbose_name_plural = "Tahlil natijalari"
        ordering = ['-calculated_at']


class Forecast(models.Model):
    METHOD_CHOICES = [
        ('ma', 'Moving Average'),
        ('es', 'Exponential Smoothing'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='forecasts')
    method = models.CharField(max_length=5, choices=METHOD_CHOICES)
    forecast_date = models.DateField()
    predicted_demand = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_demand = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    mape = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Prognoz"
        verbose_name_plural = "Prognozlar"
        ordering = ['-forecast_date']


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=200)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.IntegerField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Audit log"
        verbose_name_plural = "Audit loglar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.action} ({self.created_at})"
