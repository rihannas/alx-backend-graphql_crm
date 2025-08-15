# seed_db.py
"""
Database seeding script for CRM GraphQL project.
Run this script to populate the database with sample data.

Usage:
python seed_db.py
"""

import os
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

from crm.models import Customer, Product, Order, OrderProduct
from django.db import transaction


def clear_data():
    """Clear existing data"""
    print("Clearing existing data...")
    OrderProduct.objects.all().delete()
    Order.objects.all().delete()
    Product.objects.all().delete()
    Customer.objects.all().delete()
    print("Data cleared successfully!")


def seed_customers():
    """Seed sample customers"""
    print("Creating customers...")
    
    customers_data = [
        {
            'name': 'Alice Johnson',
            'email': 'alice@example.com',
            'phone': '+1234567890'
        },
        {
            'name': 'Bob Smith',
            'email': 'bob@example.com',
            'phone': '123-456-7890'
        },
        {
            'name': 'Carol Davis',
            'email': 'carol@example.com',
            'phone': '(555) 123-4567'
        },
        {
            'name': 'David Wilson',
            'email': 'david@example.com',
            'phone': ''
        },
        {
            'name': 'Eva Brown',
            'email': 'eva@example.com',
            'phone': '+44 20 7946 0958'
        }
    ]
    
    customers = []
    for data in customers_data:
        customer = Customer.objects.create(**data)
        customers.append(customer)
        print(f"Created customer: {customer.name}")
    
    print(f"Created {len(customers)} customers")
    return customers


def seed_products():
    """Seed sample products"""
    print("Creating products...")
    
    products_data = [
        {
            'name': 'Laptop Pro 15"',
            'price': Decimal('1299.99'),
            'stock': 25,
            'description': 'High-performance laptop with 16GB RAM and 512GB SSD'
        },
        {
            'name': 'Wireless Mouse',
            'price': Decimal('29.99'),
            'stock': 100,
            'description': 'Ergonomic wireless mouse with 3-year battery life'
        },
        {
            'name': 'Mechanical Keyboard',
            'price': Decimal('89.99'),
            'stock': 50,
            'description': 'Cherry MX Blue switches, RGB backlit'
        },
        {
            'name': 'External Monitor 24"',
            'price': Decimal('199.99'),
            'stock': 30,
            'description': '4K UHD monitor with USB-C connectivity'
        },
        {
            'name': 'USB-C Hub',
            'price': Decimal('49.99'),
            'stock': 75,
            'description': '7-in-1 USB-C hub with HDMI, USB 3.0, and SD card reader'
        },
        {
            'name': 'Wireless Headphones',
            'price': Decimal('159.99'),
            'stock': 40,
            'description': 'Noise-cancelling over-ear headphones with 30h battery'
        },
        {
            'name': 'Smartphone Case',
            'price': Decimal('19.99'),
            'stock': 200,
            'description': 'Protective case with built-in screen protector'
        },
        {
            'name': 'Portable Charger',
            'price': Decimal('39.99'),
            'stock': 60,
            'description': '10000mAh power bank with fast charging'
        }
    ]
    
    products = []
    for data in products_data:
        product = Product.objects.create(**data)
        products.append(product)
        print(f"Created product: {product.name} - ${product.price}")
    
    print(f"Created {len(products)} products")
    return products


def seed_orders(customers, products):
    """Seed sample orders"""
    print("Creating orders...")
    
    import random
    from django.utils import timezone
    from datetime import timedelta
    
    orders_created = 0
    
    # Create orders for each customer
    for customer in customers[:4]:  # Skip last customer to show variety
        num_orders = random.randint(1, 3)
        
        for _ in range(num_orders):
            # Select random products for this order
            num_products = random.randint(1, 4)
            selected_products = random.sample(products, num_products)
            
            # Create order
            order = Order.objects.create(
                customer=customer,
                order_date=timezone.now() - timedelta(days=random.randint(0, 30))
            )
            
            # Add products to order
            total_amount = Decimal('0.00')
            for product in selected_products:
                quantity = random.randint(1, 3)
                OrderProduct.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price_at_time=product.price
                )
                total_amount += product.price * quantity
            
            # Update order total
            order.total_amount = total_amount
            order.save()
            
            orders_created += 1
            print(f"Created order #{order.id} for {customer.name} - ${total_amount}")
    
    print(f"Created {orders_created} orders")


def main():
    """Main seeding function"""
    print("Starting database seeding...")
    
    with transaction.atomic():
        # Clear existing data
        clear_data()
        
        # Seed data
        customers = seed_customers()
        products = seed_products()
        seed_orders(customers, products)
    
    print("\nDatabase seeding completed successfully!")
    print("\nSummary:")
    print(f"- Customers: {Customer.objects.count()}")
    print(f"- Products: {Product.objects.count()}")
    print(f"- Orders: {Order.objects.count()}")
    print(f"- Order-Product relationships: {OrderProduct.objects.count()}")
    
    print("\nYou can now test the GraphQL mutations at: http://localhost:8000/graphql/")


if __name__ == '__main__':
    main()