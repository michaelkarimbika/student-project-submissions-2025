# Generated by Django 5.1.6 on 2025-03-15 10:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductSimilarity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('similarity_score', models.FloatField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='similarities_as_first', to='products.product')),
                ('product2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='similarities_as_second', to='products.product')),
            ],
            options={
                'unique_together': {('product1', 'product2')},
            },
        ),
        migrations.CreateModel(
            name='UserProductInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interaction_type', models.CharField(choices=[('view', 'View'), ('cart', 'Add to Cart'), ('purchase', 'Purchase'), ('review', 'Review')], max_length=10)),
                ('value', models.FloatField(default=1.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_interactions', to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_interactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'product', 'interaction_type')},
            },
        ),
        migrations.CreateModel(
            name='UserProductRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_recommendations', to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_recommendations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-score'],
                'unique_together': {('user', 'product')},
            },
        ),
    ]
