# crm/schema.py
import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import re

from .models import Customer, Product, Order, OrderProduct


# GraphQL Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"


class OrderProductType(DjangoObjectType):
    class Meta:
        model = OrderProduct
        fields = "__all__"


# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()
    description = graphene.String()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()

class CustomerFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    email_icontains = graphene.String()
    created_at_gte = graphene.DateTime()
    created_at_lte = graphene.DateTime()
    phone_pattern = graphene.String()


class ProductFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    price_gte = graphene.Decimal()
    price_lte = graphene.Decimal()
    stock_gte = graphene.Int()
    stock_lte = graphene.Int()
    stock = graphene.Int()
    low_stock = graphene.Boolean()


class OrderFilterInput(graphene.InputObjectType):
    total_amount_gte = graphene.Decimal()
    total_amount_lte = graphene.Decimal()
    order_date_gte = graphene.DateTime()
    order_date_lte = graphene.DateTime()
    customer_name = graphene.String()
    product_name = graphene.String()
    product_id = graphene.ID()


# Utility Functions
def validate_email(email):
    """Validate email format"""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        raise ValidationError("Invalid email format")


def validate_phone(phone):
    """Validate phone format"""
    if phone:
        phone_regex = r'^\+?[\d\s\-\(\)]+$'
        if not re.match(phone_regex, phone):
            raise ValidationError("Invalid phone format. Use format like '+1234567890' or '123-456-7890'")


def validate_price(price):
    """Validate price is positive"""
    if price <= 0:
        raise ValidationError("Price must be positive")


def validate_stock(stock):
    """Validate stock is non-negative"""
    if stock < 0:
        raise ValidationError("Stock cannot be negative")


# Error Types
class ErrorType(graphene.ObjectType):
    field = graphene.String()
    message = graphene.String()


class CustomerError(graphene.ObjectType):
    index = graphene.Int()
    email = graphene.String()
    errors = graphene.List(ErrorType)


# Mutation Classes
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(ErrorType)

    def mutate(self, info, input):
        errors = []
        
        try:
            # Validate email format
            validate_email(input.email)
            
            # Validate phone format
            if input.get('phone'):
                validate_phone(input.phone)
            
            # Check if email already exists
            if Customer.objects.filter(email=input.email).exists():
                errors.append(ErrorType(field="email", message="Email already exists"))
                return CreateCustomer(customer=None, message="Failed to create customer", errors=errors)
            
            # Create customer
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.get('phone', '')
            )
            
            return CreateCustomer(
                customer=customer,
                message="Customer created successfully",
                errors=[]
            )
            
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, messages in e.message_dict.items():
                    for message in messages:
                        errors.append(ErrorType(field=field, message=message))
            else:
                errors.append(ErrorType(field="general", message=str(e)))
            
            return CreateCustomer(customer=None, message="Validation failed", errors=errors)
        except Exception as e:
            errors.append(ErrorType(field="general", message=str(e)))
            return CreateCustomer(customer=None, message="Failed to create customer", errors=errors)


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(CustomerError)
    message = graphene.String()

    def mutate(self, info, input):
        created_customers = []
        errors = []
        
        with transaction.atomic():
            for i, customer_input in enumerate(input):
                customer_errors = []
                
                try:
                    # Validate email format
                    validate_email(customer_input.email)
                    
                    # Validate phone format
                    if customer_input.get('phone'):
                        validate_phone(customer_input.phone)
                    
                    # Check if email already exists
                    if Customer.objects.filter(email=customer_input.email).exists():
                        customer_errors.append(ErrorType(field="email", message="Email already exists"))
                    
                    if not customer_errors:
                        customer = Customer.objects.create(
                            name=customer_input.name,
                            email=customer_input.email,
                            phone=customer_input.get('phone', '')
                        )
                        created_customers.append(customer)
                    else:
                        errors.append(CustomerError(
                            index=i,
                            email=customer_input.email,
                            errors=customer_errors
                        ))
                        
                except ValidationError as e:
                    if hasattr(e, 'message_dict'):
                        for field, messages in e.message_dict.items():
                            for message in messages:
                                customer_errors.append(ErrorType(field=field, message=message))
                    else:
                        customer_errors.append(ErrorType(field="general", message=str(e)))
                    
                    errors.append(CustomerError(
                        index=i,
                        email=customer_input.email,
                        errors=customer_errors
                    ))
                except Exception as e:
                    customer_errors.append(ErrorType(field="general", message=str(e)))
                    errors.append(CustomerError(
                        index=i,
                        email=customer_input.email,
                        errors=customer_errors
                    ))
        
        success_count = len(created_customers)
        error_count = len(errors)
        message = f"Successfully created {success_count} customers"
        if error_count > 0:
            message += f", {error_count} failed"
        
        return BulkCreateCustomers(
            customers=created_customers,
            errors=errors,
            message=message
        )


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()
    errors = graphene.List(ErrorType)

    def mutate(self, info, input):
        errors = []
        
        try:
            # Validate price
            validate_price(input.price)
            
            # Validate stock
            stock = input.get('stock', 0)
            validate_stock(stock)
            
            # Create product
            product = Product.objects.create(
                name=input.name,
                price=input.price,
                stock=stock,
                description=input.get('description', '')
            )
            
            return CreateProduct(
                product=product,
                message="Product created successfully",
                errors=[]
            )
            
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, messages in e.message_dict.items():
                    for message in messages:
                        errors.append(ErrorType(field=field, message=message))
            else:
                errors.append(ErrorType(field="general", message=str(e)))
            
            return CreateProduct(product=None, message="Validation failed", errors=errors)
        except Exception as e:
            errors.append(ErrorType(field="general", message=str(e)))
            return CreateProduct(product=None, message="Failed to create product", errors=errors)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()
    errors = graphene.List(ErrorType)

    def mutate(self, info, input):
        errors = []
        
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(id=input.customer_id)
            except Customer.DoesNotExist:
                errors.append(ErrorType(field="customer_id", message="Customer not found"))
                return CreateOrder(order=None, message="Invalid customer", errors=errors)
            
            # Validate at least one product
            if not input.product_ids:
                errors.append(ErrorType(field="product_ids", message="At least one product is required"))
                return CreateOrder(order=None, message="No products selected", errors=errors)
            
            # Validate all products exist
            products = []
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    errors.append(ErrorType(field="product_ids", message=f"Product with ID {product_id} not found"))
            
            if errors:
                return CreateOrder(order=None, message="Invalid product IDs", errors=errors)
            
            # Create order with transaction
            with transaction.atomic():
                order = Order.objects.create(
                    customer=customer,
                    order_date=input.get('order_date', timezone.now())
                )
                
                # Add products to order and calculate total
                total_amount = Decimal('0.00')
                for product in products:
                    OrderProduct.objects.create(
                        order=order,
                        product=product,
                        quantity=1,  # Default quantity, could be extended
                        price_at_time=product.price
                    )
                    total_amount += product.price
                
                # Update order total
                order.total_amount = total_amount
                order.save()
            
            return CreateOrder(
                order=order,
                message="Order created successfully",
                errors=[]
            )
            
        except Exception as e:
            errors.append(ErrorType(field="general", message=str(e)))
            return CreateOrder(order=None, message="Failed to create order", errors=errors)


# Query Class
class Query(graphene.ObjectType):
    # Customer queries
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    
    # Product queries
    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    
    # Order queries
    orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    
    # Customer orders
    customer_orders = graphene.List(OrderType, customer_id=graphene.ID(required=True))

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None

    def resolve_orders(self, info):
        return Order.objects.all()

    def resolve_order(self, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None

    def resolve_customer_orders(self, info, customer_id):
        return Order.objects.filter(customer_id=customer_id)


# Mutation Class
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()