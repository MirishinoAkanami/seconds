from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('add/', views.item_add, name='item_add'),
    path('edit/<int:pk>/', views.item_edit, name='item_edit'),
    path('delete/<int:pk>/', views.item_delete, name='item_delete'),
    path('stock/<int:pk>/update/', views.quick_stock_update, name='quick_stock_update'),
]
