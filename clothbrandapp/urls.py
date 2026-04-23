from django.urls import path
from . import views
from .views import HomeViews , DetailViews,CategoryView, SearchView
from clothbrandapp.views import (
    initiate_payment, 
    payment_callback, 
    paystack_webhook
)


urlpatterns = [
    path('', HomeViews.as_view(), name='home'),
    path('products/', views.ProductsView.as_view(), name='products'),
    path('product/<slug:slug>/', DetailViews.as_view(), name='product_detail'),
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category'),
    path('search/', SearchView.as_view(), name='search'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/<str:action>/', views.update_cart, name='update_cart'),
# ... your other urls ...

    path('initiate/', initiate_payment, name='initiate_payment'),
    
    # Change these two lines:
    path('callback/', payment_callback, name='payment_callback'),
    path('webhook/', paystack_webhook, name='paystack_webhook'),
]