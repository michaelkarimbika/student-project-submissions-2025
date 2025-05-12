from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Address

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 
                  'phone_number', 'profile_image', 'date_of_birth', 'country', 'city', 'state', 
                  'postal_code', 'latitude', 'longitude')
        read_only_fields = ('id',)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2', 'first_name', 'last_name', 
                  'country', 'city', 'state', 'postal_code')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        
        # Create default address if location data is provided
        country = validated_data.get('country')
        city = validated_data.get('city')
        state = validated_data.get('state')
        postal_code = validated_data.get('postal_code')
        address_line1=validated_data.get('address_line1')
        
        # Only create address if at least some location data is provided
        if country or city or state or postal_code:
            Address.objects.create(
                user=user,
                address_line1=address_line1 or "",
                city=city or "",
                state=state or "",
                postal_code=postal_code or "",
                country=country or "",
                is_default=True
            )
            
        return user

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('id', 'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'is_default')
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = self.context['request'].user
        address = Address.objects.create(user=user, **validated_data)
        return address
