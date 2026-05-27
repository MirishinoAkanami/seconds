from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('guest/', views.guest_home, name='guest_home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('agreement/', views.agreement_view, name='agreement'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('announcements/new/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    path('store-settings/', views.store_settings_view, name='store_settings'),
    path('orders/', views.orders_view, name='orders'),
    path('orders/<int:pk>/update/', views.order_update, name='order_update'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('ai-debug/', views.ai_debug, name='ai_debug'),
    path('ai-models/', views.ai_list_models, name='ai_list_models'),
]
