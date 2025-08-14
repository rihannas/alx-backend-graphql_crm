import graphene
from graphene_django import DjangoObjectType, DjangoListField
from .models import Customer, Order, Product
import datetime

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

class Query(graphene.ObjectType):
    # Add some basic queries to make the Query type functional
    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)
    
    def resolve_all_customers(self, info):
        return Customer.objects.all()
    
    def resolve_all_products(self, info):
        return Product.objects.all()
    
    def resolve_all_orders(self, info):
        return Order.objects.all()
    
class CreateCustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=True)

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = graphene.List(CreateCustomerInput, required=True)


    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):  # Fixed: added 'self' parameter
        # validate email
        if Customer.objects.filter(email=input.email).exists():
            raise Exception("Email already exists")
        
        customer = Customer.objects.create(name=input.name, email=input.email, phone=input.phone)
        return CreateCustomer(customer=customer, message="Customer created successfully")



class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CreateCustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):  # Fixed: added 'self' parameter
        created = []
        errors = []
        for customer_data in input:
            try:
                # reuse single customer validation logic
                customer = Customer.objects.create(**customer_data)
                created.append(customer)
            except Exception as e:
                errors.append(str(e))
        return BulkCreateCustomers(customers=created, errors=errors)

class CreateProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.String(required=True)
    stock = graphene.Int(required=True, default_value=0)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = graphene.List(CreateProductInput, required=True)

    product = graphene.Field(ProductType)  
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        errors = []

        from decimal import Decimal, InvalidOperation
        try:
            price_decimal = Decimal(input.price)
        except (InvalidOperation, TypeError):
            errors.append("Price must be a valid decimal number.")
            return CreateProduct(product=None, errors=errors)

        # Validation
        if input.price <= 0:
            errors.append("Price must be greater than 0.")
        if input.stock < 0:
            errors.append("Stock cannot be negative.")

        if errors:
            return CreateProduct(product=None, errors=errors)

        # Create product
        product = Product.objects.create(
            name=input.name,
            price=input.price_decimal,
            stock=input.stock
        )
        return CreateProduct(product=product, errors=None)

class CreateOrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = graphene.List(CreateOrderInput, required=True)


    order = graphene.Field(OrderType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):  # Fixed: added 'self' and default value
        errors = []

        # Validate customer
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            errors.append(f"Customer with ID {input.customer_id} does not exist.")
            return CreateOrder(order=None, errors=errors)

        # Validate product list
        if not input.product_ids:
            errors.append("At least one product must be selected.")
            return CreateOrder(order=None, errors=errors)

        products = Product.objects.filter(pk__in=input.product_ids)
        if products.count() != len(input.product_ids):
            errors.append("One or more product IDs are invalid.")
            return CreateOrder(order=None, errors=errors)

        # Calculate total amount
        total_amount = sum([p.price for p in products])

        # Create order
        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount,
            order_date=input.order_date or datetime.datetime.now()  # Fixed: use datetime.datetime
        )

        # Link products
        order.products.set(products)

        return CreateOrder(order=order, errors=None)

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()