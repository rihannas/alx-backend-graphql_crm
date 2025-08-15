# crm/filters.py
import django_filters
from django_filters import FilterSet, CharFilter, DateFromToRangeFilter, NumberFilter
from django.db.models import Q
from .models import Customer, Product, Order


class CustomerFilter(FilterSet):
    """Filter for Customer model"""
    name = CharFilter(field_name='name', lookup_expr='icontains')
    email = CharFilter(field_name='email', lookup_expr='icontains')
    created_at = DateFromToRangeFilter(field_name='created_at')
    created_at_gte = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    phone_pattern = CharFilter(method='filter_phone_pattern')

    class Meta:
        model = Customer
        fields = ['name', 'email', 'created_at']

    def filter_phone_pattern(self, queryset, name, value):
        """Custom filter to match customers with specific phone number patterns"""
        if value:
            return queryset.filter(phone__startswith=value)
        return queryset


class ProductFilter(FilterSet):
    """Filter for Product model"""
    name = CharFilter(field_name='name', lookup_expr='icontains')
    price_gte = NumberFilter(field_name='price', lookup_expr='gte')
    price_lte = NumberFilter(field_name='price', lookup_expr='lte')
    stock_gte = NumberFilter(field_name='stock', lookup_expr='gte')
    stock_lte = NumberFilter(field_name='stock', lookup_expr='lte')
    stock = NumberFilter(field_name='stock', lookup_expr='exact')
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')

    class Meta:
        model = Product
        fields = ['name', 'price', 'stock']

    def filter_low_stock(self, queryset, name, value):
        """Filter products with low stock (less than 10)"""
        if value:
            return queryset.filter(stock__lt=10)
        return queryset


class OrderFilter(FilterSet):
    """Filter for Order model"""
    total_amount_gte = NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount_lte = NumberFilter(field_name='total_amount', lookup_expr='lte')
    order_date_gte = django_filters.DateFilter(field_name='order_date', lookup_expr='gte')
    order_date_lte = django_filters.DateFilter(field_name='order_date', lookup_expr='lte')
    order_date = DateFromToRangeFilter(field_name='order_date')
    customer_name = CharFilter(field_name='customer__name', lookup_expr='icontains')
    product_name = CharFilter(method='filter_by_product_name')
    product_id = NumberFilter(method='filter_by_product_id')

    class Meta:
        model = Order
        fields = ['total_amount', 'order_date', 'customer']

    def filter_by_product_name(self, queryset, name, value):
        """Filter orders by product name (case-insensitive partial match)"""
        if value:
            return queryset.filter(
                orderproduct__product__name__icontains=value
            ).distinct()
        return queryset

    def filter_by_product_id(self, queryset, name, value):
        """Filter orders that include a specific product ID"""
        if value:
            return queryset.filter(
                orderproduct__product__id=value
            ).distinct()
        return queryset