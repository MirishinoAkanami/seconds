from django.contrib import admin
from .models import SariItem, StockLog

@admin.register(SariItem)
class SariItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity', 'unit')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ('item', 'action', 'quantity_changed', 'created_at')
    list_filter = ('action',)
