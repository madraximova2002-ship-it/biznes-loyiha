from django.contrib import admin
from core.models import (
    UserProfile, Warehouse, Category, Supplier, Product,
    WarehouseStock, InventoryTransaction, AnalyticsResult,
    Forecast, AuditLog
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'created_at']
    list_filter = ['role']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'is_active']
    list_filter = ['is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'price', 'min_stock', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'sku']


@admin.register(WarehouseStock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = ['warehouse', 'product', 'quantity', 'updated_at']
    list_filter = ['warehouse']


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'product', 'warehouse', 'quantity', 'total_price', 'created_at']
    list_filter = ['transaction_type', 'warehouse']


@admin.register(AnalyticsResult)
class AnalyticsResultAdmin(admin.ModelAdmin):
    list_display = ['analysis_type', 'product', 'category_label', 'value', 'calculated_at']
    list_filter = ['analysis_type']


@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ['product', 'method', 'forecast_date', 'predicted_demand']
    list_filter = ['method']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'created_at']
    list_filter = ['action', 'model_name']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'details', 'ip_address', 'created_at']
