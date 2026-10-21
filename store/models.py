import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'
    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    short_description = models.CharField(max_length=240)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', blank=True)
    artwork = models.CharField(max_length=30, default='mug', help_text='Local illustration name, used when no image is uploaded.')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['name']
        constraints = [models.CheckConstraint(condition=models.Q(price__gt=0), name='positive_product_price')]
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse('product', args=[self.slug])

    @property
    def image_url(self):
        return reverse('product_image', args=[self.pk]) if self.image else ''

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    checkout_token = models.UUIDField(unique=True, editable=False)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    @property
    def total(self):
        return sum((item.subtotal for item in self.items.all()), Decimal('0.00'))
    @property
    def number(self):
        return str(self.reference).split('-')[0].upper()
    def get_absolute_url(self):
        return reverse('order', args=[self.reference])
    def __str__(self):
        return f'Order {self.number}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    product_name = models.CharField(max_length=160)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0), name='positive_order_quantity'),
                       models.CheckConstraint(condition=models.Q(price__gt=0), name='positive_order_price')]
    @property
    def subtotal(self):
        return self.price * self.quantity
    def __str__(self):
        return self.product_name

