from django.urls import path
from . import views

urlpatterns = [
    path('media/<path:name>', views.uploaded_image, name='uploaded_image'),
    path('health/', views.health, name='health'),
    path('product-images/<int:pk>/', views.product_image, name='product_image'),
    path('', views.products, name='products'),
    path('products/<slug:slug>/', views.product, name='product'),
    path('bag/', views.cart, name='cart'),
    path('bag/add/<int:pk>/', views.add_cart, name='add_cart'),
    path('bag/update/<int:pk>/', views.update_cart, name='update_cart'),
    path('register/', views.register, name='register'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.orders, name='orders'),
    path('orders/<uuid:reference>/', views.order, name='order'),
]


