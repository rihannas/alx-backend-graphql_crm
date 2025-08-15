# crm/models.py
from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?[\d\s\-\(\)]+$',
        message="Phone number must be entered in the format: '+999999999' or '999-999-9999'. Up to 15 digits allowed."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

    class Meta:
        ordering = ['name']


class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.price <= 0:
            raise ValidationError({'price': 'Price must be positive.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - ${self.price}"

    class Meta:
        ordering = ['name']


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    products = models.ManyToManyField(Product, through='OrderProduct')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_date = models.DateTimeField(auto_now_add=True)
    status_choices = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total(self):
        """Calculate total amount based on associated products"""
        total = sum(
            order_product.product.price * order_product.quantity 
            for order_product in self.orderproduct_set.all()
        )
        self.total_amount = total
        return total

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name} - ${self.total_amount}"

    class Meta:
        ordering = ['-order_date']


class OrderProduct(models.Model):
    """Through model for Order-Product relationship with quantity"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Store the price at the time of order
        if not self.price_at_time:
            self.price_at_time = self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x{self.quantity} in Order #{self.order.id}"

    class Meta:
        unique_together = ('order', 'product')