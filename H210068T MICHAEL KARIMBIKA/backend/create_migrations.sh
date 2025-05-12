#!/bin/bash

# Create migrations for all apps
python manage.py makemigrations users
python manage.py makemigrations products
python manage.py makemigrations orders
python manage.py makemigrations recommendations

# Apply migrations
python manage.py migrate
