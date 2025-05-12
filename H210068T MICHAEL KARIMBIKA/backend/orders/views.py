from django.conf import settings
from pesepay import Pesepay
from django.utils import timezone
#from pesepay.helpers import PaymentMethod
from rest_framework.views import APIView
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, Order
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, CheckoutSerializer
from products.models import Product
import requests 


class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_cart(self, request):
        """Get or create cart for the current user"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    
    def list(self, request):
        """Get the current user's cart"""
        cart = self.get_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def create(self, request):
        """Add item to cart"""
        cart = self.get_cart(request)
        
        # Validate request data
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        if not product_id:
            return Response(
                {'error': 'Product ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if product is in stock
        if product.stock < quantity:
            return Response(
                {'error': f'Not enough stock. Only {product.stock} available.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add to cart or update quantity
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def update(self, request, pk=None):
        """Update cart item quantity"""
        cart = self.get_cart(request)
        try:
            cart_item = CartItem.objects.get(cart=cart, id=pk)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        quantity = int(request.data.get('quantity', 1))
        
        # Check if product is in stock
        if cart_item.product.stock < quantity:
            return Response(
                {'error': f'Not enough stock. Only {cart_item.product.stock} available.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def destroy(self, request, pk=None):
        """Remove item from cart"""
        cart = self.get_cart(request)
        try:
            cart_item = CartItem.objects.get(cart=cart, id=pk)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        cart_item.delete()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CheckoutViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            try:
                cart = Cart.objects.get(user=user)
            except Cart.DoesNotExist:
                return Response({'error': 'Your cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

            if not cart.items.exists():
                return Response({'error': 'Your cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

            total_amount = cart.total_price
            shipping_cost = 5.99
            total_payment = float(total_amount) + shipping_cost

            order = Order.objects.create(
                user=user,
                full_name=serializer.validated_data['full_name'],
                email=serializer.validated_data['email'],
                phone=serializer.validated_data['phone'],
                address=serializer.validated_data['address'],
                shipping_cost=shipping_cost,
                total_amount=total_payment
            )

            # Order Items
            for item in cart.items.all():
                order.items.create(
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            cart.items.all().delete()

            # PESAPAY SETUP
            pesepay = Pesepay(
                settings.PESEPAY_API_KEY,
                settings.PESEPAY_API_SECRET
            )
            pesepay.return_url = settings.PESEPAY_CANCEL_URL
            pesepay.result_url = settings.PESEPAY_RETURN_URL

            transaction = pesepay.create_transaction(
                amount=total_payment,
                currency_code="USD",
                payment_reason=f"Order #{order.id}"
            )

            response = pesepay.initiate_transaction(transaction)

            if response.success:
                order.payment_reference = response.referenceNumber
                order.save()
                return Response({
                    "order_id": order.id,
                    "payment_url": response.redirectUrl,
                    "reference_number": response.referenceNumber
                })
            else:
                order.payment_status = 'failed'
                order.save()
                return Response({"error": response.message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentResultView(APIView):
    def post(self, request):
        reference_number = request.data.get('reference_number')
        status = request.data.get('status') 

        try:
            order = Order.objects.get(payment_reference=reference_number)
            order.payment_status = status
            order.save()
            return Response({"message": "Order updated"}, status=200)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
class PaymentStatusView(APIView):
    def get(self, request):
        reference = request.query_params.get('ref')
        if not reference:
            return Response({'error': 'Missing reference number'}, status=400)

        status_data = check_pesepay_status(reference)
        return Response(status_data)
    
def check_pesepay_status(reference_number):
    url = "https://api.pesepay.com/api/payments-engine/v1/payments/status"
    headers = {
        "Authorization": settings.PESEPAY_INTEGRATION_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "referenceNumber": reference_number
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        return {
            "status": data.get("paymentStatus"),
            "reference": reference_number,
            "raw": data
        }

    except requests.RequestException as e:
        return {
            "status": "FAILED",
            "reference": reference_number,
            "error": str(e)
        }