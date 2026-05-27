from django.urls import path
from . import views

urlpatterns = [
    path('', views.watch_list, name='watch_list'),
    path('item/<int:pk>/', views.watch_detail, name='watch_detail'),
    path('add/', views.watch_add, name='watch_add'),
    path('edit/<int:pk>/', views.watch_edit, name='watch_edit'),
    path('delete/<int:pk>/', views.watch_delete, name='watch_delete'),
    path('item/<int:pk>/order/', views.order_create, name='order_create'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-orders/<int:pk>/cancel/', views.order_cancel, name='order_cancel'),
    path('stats/', views.sales_stats, name='sales_stats'),
]
