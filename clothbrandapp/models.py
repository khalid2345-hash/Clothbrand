import secrets

from django.db import models
# Create your models here.
from datetime import timedelta, timezone
from time import timezone

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()
user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

class sliding_image(models.Model):
    image = models.ImageField(upload_to='sliding_images/')
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title or f"Sliding Image {self.id}"

# ---------------- Category field ----------------
class Category(models.Model):
    name = models.CharField(max_length=100, blank=False)
    slug = models.SlugField(max_length=200, unique=True, blank=False)
    image =models.ImageField(upload_to='product/', blank=True, null=True)
    
    def __str__(self):
        return self.name
    
   

# ---------------- Products field ----------------
class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    Product_description = models.TextField(blank=True)
    Product_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='products/')
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stock = models.PositiveIntegerField(default=0)
    sales_count = models.PositiveIntegerField(default=0)
    is_new = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    
    def is_new_product(self):
        return self.created_at >= timezone.now() - timedelta(days=7)
    
    def is_in_stock(self):
        return self.stock >= 0 and self.is_available
    
    def sales_performance(self):
        if self.sales_count >= 100:
            return 'Best Seller'
        elif self.sales_count >= 50:
            return 'Popular'
        else:
            return 'New Arrival'
    

    def __str__(self):
        return self.name



# product gallery
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')

    def __str__(self):
        return self.product.name

#carrt
#from django.db import models

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    )

    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField(blank=True)

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total(self):
     total = sum(item.subtotal() for item in self.items.all())
     self.total_price = total
     self.save()

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"
    
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey('Product', on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"   
    
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.PositiveIntegerField()  # in kobo (e.g. 5000 = ₦50)
    ref = models.CharField(max_length=200, unique=True)
    email = models.EmailField()
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.ref} - ₦{self.amount/100}"

    def save(self, *args, **kwargs):
        while not self.ref:
            ref = secrets.token_urlsafe(50)
            if not Payment.objects.filter(ref=ref).exists():
                self.ref = ref
        super().save(*args, **kwargs)    