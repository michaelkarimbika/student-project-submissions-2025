from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, OrderViewSet, CheckoutViewSet, PaymentResultView,PaymentStatusView
from .views import CheckoutViewSet
router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'checkout', CheckoutViewSet, basename='checkout')
#router.register(r'checkout', CheckoutViewSet, basename='checkout')
urlpatterns = [
    path('', include(router.urls)),
    path('payment-result/', PaymentResultView.as_view(), name='payment-result'),
    path('api/payment-status/', PaymentStatusView.as_view(), name='payment-status'),
    path('cart/', CartViewSet.as_view({
        'get': 'list',
        'post': 'create',
    })),
    path('cart/<int:pk>/', CartViewSet.as_view({
        'put': 'update',
        'delete': 'destroy',
    })),
]

