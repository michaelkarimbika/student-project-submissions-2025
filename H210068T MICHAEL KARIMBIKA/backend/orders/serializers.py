from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from products.serializers import ProductSerializer
from products.models import Product

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(write_only=True, source='product', queryset=Product.objects.all())
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_id', 'quantity', 'total_price', 'added_at')
        read_only_fields = ('id', 'added_at')

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Cart
        fields = ('id', 'items', 'total_price', 'item_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'quantity', 'price', 'total_price')
        read_only_fields = ('id', 'product_name', 'total_price')
    
    def get_product_name(self, obj):
        return obj.product.name

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'full_name', 'email', 'phone', 'address', 'status', 'payment_status', 
                  'payment_method', 'payment_reference', 'shipping_cost', 'total_amount', 
                  'items', 'created_at', 'updated_at')
        read_only_fields = ('id', 'status', 'payment_status', 'payment_reference', 'created_at', 'updated_at')

class CheckoutSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField()
    
    # Order items from cart
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            allow_empty=False
        ),
        required=True
    )
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required")
        for item in value:
            if 'productId' not in item or 'quantity' not in item:
                raise serializers.ValidationError("Each item must have productId and quantity")
            if item['quantity'] <= 0:
                raise serializers.ValidationError("Quantity must be greater than 0")
        return value

