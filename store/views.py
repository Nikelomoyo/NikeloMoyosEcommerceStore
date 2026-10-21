import uuid
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .cart import Cart
from .forms import CheckoutForm, QuantityForm, RegistrationForm
from .models import Category, Order, OrderItem, Product

def products(request):
    items = Product.objects.filter(available=True, stock__gt=0).select_related('category')
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category:
        items = items.filter(category__slug=category)
    sort = request.GET.get('sort', 'name')
    items = items.order_by({'price': 'price', '-price': '-price', 'new': '-created_at'}.get(sort, 'name'))
    page = Paginator(items, 8).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'store/products.html', {'page_obj': page, 'categories': Category.objects.all(),
        'query': query, 'selected_category': category, 'sort': sort, 'filter_params': params.urlencode()})

def product(request, slug):
    item = get_object_or_404(Product.objects.select_related('category'), slug=slug, available=True)
    return render(request, 'store/product.html', {'product': item})

def cart(request):
    basket = Cart(request)
    existing = set(str(pk) for pk in Product.objects.filter(pk__in=basket.data).values_list('pk', flat=True))
    missing = set(basket.data) - existing
    for pk in missing:
        basket.remove(pk)
    if missing:
        messages.info(request, 'A product is no longer sold and was removed from your bag.')
    lines = basket.lines
    return render(request, 'store/cart.html', {'lines': lines, 'total': basket.total,
        'can_checkout': bool(lines) and all(line['valid'] for line in lines) and len(lines) == len(basket.data)})

@require_POST
def add_cart(request, pk):
    item = get_object_or_404(Product, pk=pk, available=True)
    form = QuantityForm(request.POST)
    basket = Cart(request)
    if form.is_valid():
        quantity = basket.data.get(str(pk), 0) + form.cleaned_data['quantity']
        if quantity <= item.stock and quantity <= 999:
            basket.set(item, quantity)
            messages.success(request, f'{item.name} added to your bag.')
            return redirect('cart')
        messages.error(request, f'Only {item.stock} available. Your bag has not changed.')
    else:
        messages.error(request, 'Choose a whole quantity between 1 and 999.')
    return redirect(item)

@require_POST
def update_cart(request, pk):
    basket = Cart(request)
    if request.POST.get('action') == 'remove':
        basket.remove(pk)
        messages.success(request, 'Item removed from your bag.')
    else:
        item = get_object_or_404(Product, pk=pk)
        form = QuantityForm(request.POST)
        if str(pk) not in basket.data:
            messages.error(request, 'This item is no longer in your bag.')
        elif form.is_valid() and item.available and form.cleaned_data['quantity'] <= item.stock:
            basket.set(item, form.cleaned_data['quantity'])
            messages.success(request, 'Quantity updated.')
        else:
            messages.error(request, f'Choose a valid quantity. Currently available: {item.stock if item.available else 0}.')
    return redirect('cart')

def register(request):
    if request.user.is_authenticated:
        return redirect('products')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome to Everyday. Your account is ready.')
        return redirect('cart' if Cart(request).count else 'products')
    return render(request, 'registration/register.html', {'form': form})

class CheckoutError(Exception):
    pass

@login_required
def checkout(request):
    basket = Cart(request)
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            previous = Order.objects.filter(checkout_token=token, user=request.user).first()
            if previous:
                return redirect(previous)
            if str(token) != request.session.get('checkout_token'):
                form.add_error(None, 'This checkout has expired. Open checkout again from your bag.')
            else:
                try:
                    with transaction.atomic():
                        # This first write serializes SQLite checkouts. PostgreSQL also locks products below.
                        order = form.save(commit=False)
                        order.user = request.user
                        order.checkout_token = token
                        order.save()
                        if not basket.data:
                            raise CheckoutError('Your bag is empty.')
                        items = list(Product.objects.select_for_update().filter(pk__in=basket.data).order_by('pk'))
                        if len(items) != len(basket.data):
                            raise CheckoutError('A product was removed. Please review your bag.')
                        for item in items:
                            quantity = basket.data[str(item.pk)]
                            updated = Product.objects.filter(pk=item.pk, available=True, stock__gte=quantity).update(stock=F('stock') - quantity)
                            if not updated:
                                raise CheckoutError(f'{item.name} has insufficient stock. Please review your bag.')
                            OrderItem.objects.create(order=order, product=item, product_name=item.name,
                                                     price=item.price, quantity=quantity)
                    basket.clear()
                    request.session.pop('checkout_token', None)
                    messages.success(request, 'Order placed successfully. This was a mock payment; no money was charged.')
                    return redirect(order)
                except CheckoutError as error:
                    form.add_error(None, str(error))
                except IntegrityError:
                    previous = Order.objects.filter(checkout_token=token, user=request.user).first()
                    if previous:
                        return redirect(previous)
                    form.add_error(None, 'We could not place this order. Please review your bag and try again.')
                except OperationalError:
                    form.add_error(None, 'The store is busy. Please retry; your bag is preserved.')
    else:
        if not basket.count:
            return redirect('cart')
        token = request.session.setdefault('checkout_token', str(uuid.uuid4()))
        form = CheckoutForm(initial={'token': token, 'name': request.user.get_full_name(), 'email': request.user.email})
    return render(request, 'store/checkout.html', {'form': form, 'lines': basket.lines, 'total': basket.total})

@login_required
def orders(request):
    page = Paginator(Order.objects.filter(user=request.user).prefetch_related('items'), 10).get_page(request.GET.get('page'))
    return render(request, 'store/orders.html', {'page_obj': page})

@login_required
def order(request, reference):
    item = get_object_or_404(Order.objects.prefetch_related('items'), reference=reference, user=request.user)
    return render(request, 'store/order.html', {'order': item})


# Public product uploads are served by database identity, never an arbitrary path.
def product_image(request, pk):
    from django.http import FileResponse, Http404
    from PIL import Image, UnidentifiedImageError
    item = get_object_or_404(Product, pk=pk, available=True)
    if not item.image:
        raise Http404('No product image.')
    source = None
    try:
        source = item.image.open('rb')
        picture = Image.open(source)
        mime = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp', 'GIF': 'image/gif'}.get(picture.format)
        if not mime:
            raise ValueError('Unsupported image type')
        source.seek(0)
    except (OSError, ValueError, UnidentifiedImageError):
        if source is not None:
            source.close()
        raise Http404('Image unavailable.')
    response = FileResponse(source, content_type=mime)
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'public, max-age=300'
    return response


def health(request):
    from django.db import connection
    from django.http import JsonResponse
    # Verify database availability without querying private customer records.
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()
    return JsonResponse({'status': 'ok'})


def uploaded_image(request, name):
    item = get_object_or_404(Product, image=name, available=True)
    return product_image(request, item.pk)
