import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_ecommerce.settings')
django.setup()

from apps.menu_app.models import MenuItem

with open('item_output.txt', 'w') as f:
    try:
        items = MenuItem.objects.filter(name__icontains='Chicken Dum Biryani')
        for item in items:
            f.write(f"Name: {item.name}\n")
            f.write(f"Price: {item.price}\n")
            f.write(f"Image: {item.image.url if item.image else 'No Image'}\n")
            f.write(f"Description: {item.description}\n")
            f.write("-" * 20 + "\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
