from django.urls import path
from core import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('toggle-theme/', views.toggle_view, name='toggle_theme'),

    # Warehouses
    path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('warehouses/create/', views.warehouse_create, name='warehouse_create'),
    path('warehouses/<int:pk>/edit/', views.warehouse_edit, name='warehouse_edit'),
    path('warehouses/<int:pk>/delete/', views.warehouse_delete, name='warehouse_delete'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/import/', views.product_import_excel, name='product_import_excel'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),

    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/invoice/', views.transaction_invoice, name='transaction_invoice'),

    # Analytics
    path('analytics/', views.analytics_view, name='analytics'),

    # Optimization
    path('optimization/', views.optimization_view, name='optimization'),

    # Forecast
    path('forecast/', views.forecast_view, name='forecast'),

    # Reports
    path('reports/', views.reports_view, name='reports'),
    path('reports/daily/', views.report_daily, name='report_daily'),
    path('reports/export/excel/', views.export_excel, name='export_excel'),
    path('reports/export/pdf/', views.export_pdf, name='export_pdf'),

    # Audit
    path('audit/', views.audit_log_view, name='audit_log'),

    # API
    path('api/dashboard/', views.api_dashboard_data, name='api_dashboard'),
    path('api/notifications/', views.api_notifications, name='api_notifications'),
]
