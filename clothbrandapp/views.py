from django.shortcuts import render
from django.views import View
from .models import Payment, Product, Category, sliding_image
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Payment
import requests
import json
import hmac
import hashlib

class HomeViews(View):
    def get(self, request):
        sliding_images = sliding_image.objects.all()        
        products = Product.objects.filter(is_available=True).order_by('-created_at')
        categories = Category.objects.all()
        
        return render(request, 'home.html', {
            'products': products,
            'categories': categories,
            'sliding_images': sliding_images
        })
    
class ProductsView(View):
    def get(self, request):
        products = Product.objects.all()
        categories = Category.objects.all()
        
        return render(request, 'khalidapp/products.html', {
            'products': products,
            'categories': categories,
            
        })



class DetailViews(View):
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        categories = Category.objects.all()
        return render(request, 'detail.html', {'product': product,'categories': categories,})
    
class CategoryView(View):
    def get(self, request, slug):
        
        category = get_object_or_404(Category, slug=slug)
        categories = Category.objects.all()
        products = Product.objects.filter(category=category)

        paginator = Paginator(products, 8)
        page = request.GET.get('page')
        products = paginator.get_page(page)


        return render(request, 'category.html', {
            
            'category': category,
            'products': products,
            'categories': categories,
        })
    
class SearchView(View):
    def get(self, request):
        query = request.GET.get('q','')
        products = Product.objects.filter(name__icontains=query)
        categories = Category.objects.all()
        return render(request, 'search_result.html', { 'products': products, 'categories': categories })    
        
# ADD CART VIEWS

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    cart = request.session.get('cart', {})
    
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1
    
    request.session['cart'] = cart
    request.session.modified = True

    # Return JSON instead of redirect
    return JsonResponse({
        'success': True,
        'message': f'{product.name} added to cart',
        'cart_count': sum(cart.values()),  # total items in cart
        'product_id': product_id
    })


def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)

        subtotal = product.Product_price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
        'categories': Category.objects.all()
    })

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]

    request.session['cart'] = cart
    request.session.modified = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'message': 'Item removed'})

    return redirect('view_cart')

def update_cart(request, product_id, action):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:

        if action == "increase":
            cart[str(product_id)] += 1

        elif action == "decrease":
            cart[str(product_id)] -= 1

            if cart[str(product_id)] <= 0:
                del cart[str(product_id)]

    request.session['cart'] = cart
    return redirect('view_cart')

def cart_count(request):
    cart = request.session.get('cart', {})
    return {'cart_count': sum(cart.values())}     

# Payment Views will be added here in the future
def initiate_payment(request):
    if request.method == "POST":
        amount = int(request.POST.get('amount')) * 100  # Convert to kobo
        email = request.POST.get('email') or request.user.email if request.user.is_authenticated else None

        if not email:
            # Handle error
            return render(request, 'payment/initiate.html', {'error': 'Email required'})

        # Create payment record
        payment = Payment.objects.create(
            amount=amount,
            email=email,
            user=request.user if request.user.is_authenticated else None
        )

        # Initialize Paystack transaction
        url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        data = {
            "email": email,
            "amount": amount,
            "reference": payment.ref,
            "callback_url": request.build_absolute_uri('/payment/callback/'),
            # Optional
            "metadata": {
                "user_id": str(request.user.id) if request.user.is_authenticated else None,
                "custom_fields": [{"display_name": "Product", "variable_name": "product", "value": "Premium Plan"}]
            }
        }

        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if response_data.get('status'):
            authorization_url = response_data['data']['authorization_url']
            return redirect(authorization_url)
        else:
            # Handle error
            return render(request, 'payment/initiate.html', {'error': response_data.get('message')})

    return render(request, 'payment/initiate.html')

def initiate_payment(request):
    return render(request, 'payment/initiate.html', {
        'PAYSTACK_PUBLIC_KEY': settings.PAYSTACK_PUBLIC_KEY
    })

def payment_callback(request):
    reference = request.GET.get('reference')
    
    if not reference:
        return render(request, 'payment/failed.html', {'error': 'No reference provided'})

    # Verify the transaction with Paystack
    url = f'https://api.paystack.co/transaction/verify/{reference}'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
    }

    try:
        response = requests.get(url, headers=headers)   # ← This was the bug
        response_data = response.json()

        if response_data.get('status') and response_data['data']['status'] == 'success':
            # Payment successful
            payment = get_object_or_404(Payment, ref=reference)
            payment.verified = True
            payment.save()

            return render(request, 'payment/success.html', {'payment': payment})
        
        else:
            # Payment failed or not successful
            return render(request, 'payment/failed.html', {
                'error': response_data.get('message', 'Payment verification failed')
            })

    except Exception as e:
        return render(request, 'payment/failed.html', {'error': str(e)})
    
@csrf_exempt
def paystack_webhook(request):
    # Verify signature
    paystack_signature = request.headers.get('x-paystack-signature')
    if not paystack_signature:
        return HttpResponse(status=400)

    # Get raw body
    body = request.body
    secret = settings.PAYSTACK_SECRET_KEY.encode()

    # Verify HMAC
    computed_signature = hmac.new(secret, body, hashlib.sha512).hexdigest()
    if computed_signature != paystack_signature:
        return HttpResponse(status=403)

    # Process event
    event = json.loads(body)
    
    if event['event'] == 'charge.success':
        reference = event['data']['reference']
        try:
            payment = Payment.objects.get(ref=reference)
            if not payment.verified:
                payment.verified = True
                payment.save()
                # Trigger order fulfillment, email, etc.
        except Payment.DoesNotExist:
            pass  # Log it

    return HttpResponse(status=200)    

# Create your views here.
