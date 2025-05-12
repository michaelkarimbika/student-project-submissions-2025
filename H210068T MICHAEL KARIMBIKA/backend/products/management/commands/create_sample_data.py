from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Product, ProductImage, Review, Season
from recommendations.recommendation_engine import RecommendationEngine
import random
from django.utils.text import slugify

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample data for the e-commerce recommendation system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write(self.style.SUCCESS('Superuser created'))
        
        # Create seasons
        seasons_data = [
            {'name': 'Winter', 'start_month': 12, 'end_month': 2, 'hemisphere': 'N'},
            {'name': 'Spring', 'start_month': 3, 'end_month': 5, 'hemisphere': 'N'},
            {'name': 'Summer', 'start_month': 6, 'end_month': 8, 'hemisphere': 'N'},
            {'name': 'Fall', 'start_month': 9, 'end_month': 11, 'hemisphere': 'N'},
            {'name': 'Winter', 'start_month': 6, 'end_month': 8, 'hemisphere': 'S'},
            {'name': 'Spring', 'start_month': 9, 'end_month': 11, 'hemisphere': 'S'},
            {'name': 'Summer', 'start_month': 12, 'end_month': 2, 'hemisphere': 'S'},
            {'name': 'Fall', 'start_month': 3, 'end_month': 5, 'hemisphere': 'S'},
            {'name': 'Holiday Season', 'start_month': 11, 'end_month': 12, 'hemisphere': 'B'},
        ]
        
        for season_data in seasons_data:
            season, created = Season.objects.get_or_create(
                name=season_data['name'],
                hemisphere=season_data['hemisphere'],
                defaults={
                    'start_month': season_data['start_month'],
                    'end_month': season_data['end_month'],
                }
            )
            if created:
                self.stdout.write(f'Created season: {season.name} ({season.hemisphere})')
        
        # Create categories
        categories = [
            {'name': 'Electronics', 'description': 'Electronic devices and accessories'},
            {'name': 'Clothing', 'description': 'Apparel and fashion items'},
            {'name': 'Home & Kitchen', 'description': 'Home appliances and kitchen essentials'},
            {'name': 'Beauty & Personal Care', 'description': 'Beauty products and personal care items'},
            {'name': 'Sports & Outdoors', 'description': 'Sports equipment and outdoor gear'},
        ]
        
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'slug': slugify(category_data['name']),
                    'description': category_data['description']
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Get all categories and seasons
        all_categories = Category.objects.all()
        winter_n = Season.objects.get(name='Winter', hemisphere='N')
        spring_n = Season.objects.get(name='Spring', hemisphere='N')
        summer_n = Season.objects.get(name='Summer', hemisphere='N')
        fall_n = Season.objects.get(name='Fall', hemisphere='N')
        holiday = Season.objects.get(name='Holiday Season')
        
        # Create products with seasonal and location data
        products_data = [
            # Electronics - mostly not seasonal
            {'name': 'Wireless Headphones', 'price': 89.99, 'category': 'Electronics', 'featured': True, 'seasons': [], 'countries': ''},
            {'name': 'Smart Watch', 'price': 199.99, 'category': 'Electronics', 'featured': True, 'seasons': [], 'countries': ''},
            {'name': 'Fitness Tracker', 'price': 49.99, 'category': 'Electronics', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Bluetooth Speaker', 'price': 79.99, 'category': 'Electronics', 'featured': False, 'seasons': [summer_n], 'countries': ''},
            {'name': 'Smartphone Stand', 'price': 19.99, 'category': 'Electronics', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Wireless Charger', 'price': 29.99, 'category': 'Electronics', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Laptop Sleeve', 'price': 24.99, 'category': 'Electronics', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Noise Cancelling Earbuds', 'price': 129.99, 'category': 'Electronics', 'featured': True, 'seasons': [], 'countries': ''},
            
            # Clothing - very seasonal
            {'name': 'Men\'s T-Shirt', 'price': 19.99, 'category': 'Clothing', 'featured': False, 'seasons': [spring_n, summer_n], 'countries': ''},
            {'name': 'Women\'s Jeans', 'price': 49.99, 'category': 'Clothing', 'featured': True, 'seasons': [fall_n, winter_n], 'countries': ''},
            {'name': 'Running Shoes', 'price': 89.99, 'category': 'Clothing', 'featured': False, 'seasons': [spring_n, summer_n], 'countries': ''},
            {'name': 'Winter Jacket', 'price': 129.99, 'category': 'Clothing', 'featured': True, 'seasons': [fall_n, winter_n], 'countries': ''},
            {'name': 'Casual Socks', 'price': 9.99, 'category': 'Clothing', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Baseball Cap', 'price': 14.99, 'category': 'Clothing', 'featured': False, 'seasons': [spring_n, summer_n], 'countries': ''},
            {'name': 'Swimsuit', 'price': 34.99, 'category': 'Clothing', 'featured': True, 'seasons': [summer_n], 'countries': ''},
            {'name': 'Scarf', 'price': 24.99, 'category': 'Clothing', 'featured': False, 'seasons': [fall_n, winter_n], 'countries': ''},
            
            # Home & Kitchen - some seasonal
            {'name': 'Coffee Maker', 'price': 69.99, 'category': 'Home & Kitchen', 'featured': True, 'seasons': [], 'countries': ''},
            {'name': 'Blender', 'price': 49.99, 'category': 'Home & Kitchen', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Toaster', 'price': 29.99, 'category': 'Home & Kitchen', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Cookware Set', 'price': 149.99, 'category': 'Home & Kitchen', 'featured': True, 'seasons': [holiday], 'countries': ''},
            {'name': 'Knife Set', 'price': 79.99, 'category': 'Home & Kitchen', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Electric Blanket', 'price': 59.99, 'category': 'Home & Kitchen', 'featured': False, 'seasons': [fall_n, winter_n], 'countries': ''},
            {'name': 'Portable Fan', 'price': 29.99, 'category': 'Home & Kitchen', 'featured': True, 'seasons': [summer_n], 'countries': ''},
            
            # Beauty & Personal Care - some seasonal
            {'name': 'Face Moisturizer', 'price': 24.99, 'category': 'Beauty & Personal Care', 'featured': False, 'seasons': [winter_n], 'countries': ''},
            {'name': 'Shampoo', 'price': 12.99, 'category': 'Beauty & Personal Care', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Electric Toothbrush', 'price': 59.99, 'category': 'Beauty & Personal Care', 'featured': True, 'seasons': [], 'countries': ''},
            {'name': 'Hair Dryer', 'price': 39.99, 'category': 'Beauty & Personal Care', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Sunscreen', 'price': 15.99, 'category': 'Beauty & Personal Care', 'featured': True, 'seasons': [spring_n, summer_n], 'countries': ''},
            
            # Sports & Outdoors - very seasonal
            {'name': 'Yoga Mat', 'price': 29.99, 'category': 'Sports & Outdoors', 'featured': True, 'seasons': [], 'countries': ''},
            {'name': 'Dumbbells Set', 'price': 79.99, 'category': 'Sports & Outdoors', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Water Bottle', 'price': 14.99, 'category': 'Sports & Outdoors', 'featured': False, 'seasons': [], 'countries': ''},
            {'name': 'Hiking Backpack', 'price': 89.99, 'category': 'Sports & Outdoors', 'featured': True, 'seasons': [spring_n, summer_n, fall_n], 'countries': ''},
            {'name': 'Ski Goggles', 'price': 49.99, 'category': 'Sports & Outdoors', 'featured': False, 'seasons': [winter_n], 'countries': 'US,CA,CH,AT,FR,IT'},
            {'name': 'Beach Umbrella', 'price': 39.99, 'category': 'Sports & Outdoors', 'featured': True, 'seasons': [summer_n], 'countries': 'US,AU,ES,IT,GR'},
            {'name': 'Tennis Racket', 'price': 69.99, 'category': 'Sports & Outdoors', 'featured': False, 'seasons': [spring_n, summer_n], 'countries': ''},
        ]
        
        for product_data in products_data:
            category = Category.objects.get(name=product_data['category'])
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults={
                    'slug': slugify(product_data['name']),
                    'description': f"This is a {product_data['name']} in the {category.name} category.",
                    'price': product_data['price'],
                    'category': category,
                    'stock': random.randint(10, 100),
                    'featured': product_data['featured'],
                    'is_location_specific': bool(product_data['countries']),
                    'available_countries': product_data['countries'],
                }
            )
            
            if created:
                # Add seasonal data
                for season in product_data['seasons']:
                    product.seasons.add(season)
                
                # Create a product image
                ProductImage.objects.create(
                    product=product,
                    image=f"/placeholder.svg?height=300&width=300",
                    alt_text=product.name,
                    is_primary=True
                )
                self.stdout.write(f'Created product: {product.name}')
        
        # Create users with location data
        users_data = [
            {'username': 'user1', 'email': 'user1@example.com', 'password': 'password123', 'country': 'US', 'state': 'CA'},
            {'username': 'user2', 'email': 'user2@example.com', 'password': 'password123', 'country': 'US', 'state': 'NY'},
            {'username': 'user3', 'email': 'user3@example.com', 'password': 'password123', 'country': 'AU', 'state': 'NSW'},
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'country': user_data['country'],
                    'state': user_data['state'],
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'Created user: {user.username} from {user.country}, {user.state}')
        
        # Create reviews
        all_users = User.objects.filter(username__in=[u['username'] for u in users_data])
        all_products = Product.objects.all()
        
        for user in all_users:
            # Each user reviews 5 random products
            for product in random.sample(list(all_products), 5):
                review, created = Review.objects.get_or_create(
                    user=user,
                    product=product,
                    defaults={
                        'rating': random.randint(3, 5),
                        'comment': f"This is a review for {product.name} by {user.username}. It's a great product!",
                        'helpful_count': random.randint(0, 10)
                    }
                )
                if created:
                    self.stdout.write(f'Created review: {user.username} -> {product.name}')
        
        # Generate recommendations
        self.stdout.write('Generating recommendations...')
        RecommendationEngine.update_user_product_interactions()
        RecommendationEngine.calculate_product_similarities()
        
        for user in all_users:
            RecommendationEngine.generate_recommendations_for_user(user)
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))

