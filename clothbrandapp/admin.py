from django.contrib import admin

# Register your models here.
from .models import OrderItem, Product, Category, sliding_image,Payment
admin.site.register(sliding_image)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(OrderItem)
admin.site.register(Payment)

