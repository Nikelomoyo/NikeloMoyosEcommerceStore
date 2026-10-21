from decimal import Decimal
from .models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get('cart', {})
    def save(self):
        self.session['cart'] = self.data
        self.session.modified = True
    def set(self, product, quantity):
        self.data[str(product.pk)] = quantity
        self.save()
    def remove(self, pk):
        self.data.pop(str(pk), None)
        self.save()
    def clear(self):
        self.data = {}
        self.save()
    @property
    def count(self):
        return sum(self.data.values())
    @property
    def lines(self):
        products = Product.objects.filter(pk__in=self.data).select_related('category')
        return [{'product': p, 'quantity': self.data[str(p.pk)],
                 'subtotal': p.price * self.data[str(p.pk)],
                 'valid': p.available and p.stock >= self.data[str(p.pk)]} for p in products]
    @property
    def total(self):
        return sum((line['subtotal'] for line in self.lines), Decimal('0.00'))

def cart_context(request):
    return {'cart_count': Cart(request).count}
