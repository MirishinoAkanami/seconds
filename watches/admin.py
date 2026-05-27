from django.contrib import admin
from .models import WatchItem, Order

@admin.register(WatchItem)
class WatchItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'condition', 'stock_quantity', 'is_available')
    list_filter = ('condition', 'is_available')
    search_fields = ('name', 'brand')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'watch_item', 'payment_method', 'delivery_option', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'delivery_option')
