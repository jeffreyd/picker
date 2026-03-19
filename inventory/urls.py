from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Items
    path('items/', views.item_list, name='item_list'),
    path('items/add/', views.item_create, name='item_create'),
    path('items/<int:pk>/', views.item_detail, name='item_detail'),
    path('items/<int:pk>/edit/', views.item_edit, name='item_edit'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('items/<int:pk>/status/', views.item_status_update, name='item_status_update'),

    # Parts
    path('parts/', views.part_list, name='part_list'),
    path('parts/add/', views.part_create, name='part_create'),
    path('parts/<int:pk>/', views.part_detail, name='part_detail'),
    path('parts/<int:pk>/edit/', views.part_edit, name='part_edit'),
    path('parts/<int:pk>/delete/', views.part_delete, name='part_delete'),

    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/add/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('orders/<int:pk>/status/', views.order_status_update, name='order_status_update'),

    # Sales
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/add/', views.sale_create, name='sale_create'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/edit/', views.sale_edit, name='sale_edit'),
    path('sales/<int:pk>/delete/', views.sale_delete, name='sale_delete'),

    # Model Notes
    path('model-notes/', views.modelnote_list, name='modelnote_list'),
    path('model-notes/add/', views.modelnote_create, name='modelnote_create'),
    path('model-notes/<int:pk>/', views.modelnote_detail, name='modelnote_detail'),
    path('model-notes/<int:pk>/edit/', views.modelnote_edit, name='modelnote_edit'),
    path('model-notes/<int:pk>/delete/', views.modelnote_delete, name='modelnote_delete'),

    # Auctions
    path('auctions/', views.auction_list, name='auction_list'),
    path('auctions/add/', views.auction_create, name='auction_create'),
    path('auctions/<int:pk>/', views.auction_detail, name='auction_detail'),
    path('auctions/<int:pk>/edit/', views.auction_edit, name='auction_edit'),
    path('auctions/<int:pk>/delete/', views.auction_delete, name='auction_delete'),
    path('auctions/<int:pk>/convert/', views.auction_convert, name='auction_convert'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]
