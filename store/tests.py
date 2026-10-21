import uuid
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from .models import Category, Product, Order, OrderItem

class StoreTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Home', slug='home')
        cls.product = Product.objects.create(category=cls.category, name='Morning mug', slug='mug',
            short_description='A good mug', description='Stoneware mug', price='249.00', stock=5)
        cls.user = User.objects.create_user('shopper', 'shopper@example.com', 'Sensible-Test-Pass-2026!')
        cls.other = User.objects.create_user('other', 'other@example.com', 'Different-Test-Pass-2026!')

    def add(self, quantity=1, product=None):
        return self.client.post(reverse('add_cart', args=[(product or self.product).pk]), {'quantity': quantity})

    def checkout_data(self):
        self.client.force_login(self.user)
        self.client.get(reverse('checkout'))
        return {'token': self.client.session['checkout_token'], 'name': 'Test Customer',
                'email': 'test@example.com', 'phone': '+27 82 123 4567',
                'address': '10 Example Street, Cape Town, 8001'}

    def test_catalog_search_filter_and_pagination(self):
        for i in range(10):
            Product.objects.create(category=self.category, name=f'Item {i}', slug=f'item-{i}',
                                   price=10, stock=1, description='Useful thing')
        response = self.client.get('/')
        self.assertEqual(len(response.context['page_obj']), 8)
        self.assertEqual(response.context['page_obj'].paginator.count, 11)
        self.assertEqual(len(self.client.get('/?page=2').context['page_obj']), 3)
        self.assertContains(self.client.get('/?q=Stoneware&category=home'), 'Morning mug')
        self.assertEqual(self.client.get('/?category=missing').context['page_obj'].paginator.count, 0)
        self.assertEqual(self.client.get('/?q=missing').context['page_obj'].paginator.count, 0)

    def test_unavailable_and_zero_stock_hidden(self):
        self.product.stock = 0
        self.product.save()
        self.assertEqual(self.client.get('/').context['page_obj'].paginator.count, 0)
        self.assertContains(self.client.get(self.product.get_absolute_url()), 'Currently out of stock')
        self.product.available = False
        self.product.save()
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 404)

    def test_product_detail(self):
        self.assertContains(self.client.get(self.product.get_absolute_url()), 'Stoneware mug')

    def test_cart_add_accumulate_update_remove(self):
        self.add(2)
        self.add(1)
        self.assertEqual(self.client.session['cart'][str(self.product.pk)], 3)
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.context['total'], Decimal('747.00'))
        self.client.post(reverse('update_cart', args=[self.product.pk]), {'quantity': 2, 'action': 'update'})
        self.assertEqual(self.client.session['cart'][str(self.product.pk)], 2)
        self.client.post(reverse('update_cart', args=[self.product.pk]), {'action': 'remove'})
        self.assertEqual(self.client.session['cart'], {})

    def test_cart_persists_across_requests(self):
        self.add(2)
        self.client.get('/')
        self.assertEqual(self.client.get(reverse('cart')).context['cart_count'], 2)

    def test_invalid_cart_quantities_do_not_mutate(self):
        for quantity in ['-1', '0', '1.5', 'nope', '6', '1000']:
            self.add(quantity)
            self.assertFalse(self.client.session.get('cart'))
        self.add(2)
        self.client.post(reverse('update_cart', args=[self.product.pk]), {'quantity': 8})
        self.assertEqual(self.client.session['cart'][str(self.product.pk)], 2)

    def test_cart_actions_require_post(self):
        self.assertEqual(self.client.get(reverse('add_cart', args=[self.product.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse('update_cart', args=[self.product.pk])).status_code, 405)

    def test_csrf_enforced(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse('add_cart', args=[self.product.pk]), {'quantity': 1}).status_code, 403)

    def test_registration_hashes_password_and_keeps_cart(self):
        self.add()
        response = self.client.post(reverse('register'), {'username': 'new-user', 'email': 'new@example.com',
            'password1': 'Unique-Strong-Pass-832!', 'password2': 'Unique-Strong-Pass-832!'})
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='new-user')
        self.assertTrue(user.check_password('Unique-Strong-Pass-832!'))
        self.assertNotEqual(user.password, 'Unique-Strong-Pass-832!')
        self.assertEqual(self.client.session['cart'][str(self.product.pk)], 1)

    def test_registration_rejects_weak_password(self):
        response = self.client.post(reverse('register'), {'username': 'weak', 'email': 'weak@example.com',
                                                        'password1': '123', 'password2': '123'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='weak').exists())

    def test_login_preserves_cart_and_logout_is_post(self):
        self.add(2)
        response = self.client.post(reverse('login'), {'username': 'shopper', 'password': 'Sensible-Test-Pass-2026!'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['cart'][str(self.product.pk)], 2)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertEqual(self.client.post(reverse('logout')).status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_login(self):
        self.assertContains(self.client.post(reverse('login'), {'username': 'shopper', 'password': 'wrong'}),
                            'Please enter a correct username and password')

    def test_checkout_requires_login(self):
        self.add()
        self.assertRedirects(self.client.get(reverse('checkout')), reverse('login') + '?next=/checkout/')

    def test_checkout_server_total_and_snapshots(self):
        self.add(2)
        data = self.checkout_data()
        data.update({'price': '0.01', 'total': '0.02', 'status': 'delivered'})
        response = self.client.post(reverse('checkout'), data)
        order = Order.objects.get()
        self.assertRedirects(response, order.get_absolute_url())
        self.assertEqual(order.total, Decimal('498.00'))
        self.assertEqual(order.status, 'pending')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(self.client.session['cart'], {})
        self.product.price = 999
        self.product.name = 'Changed name'
        self.product.save()
        self.assertEqual(order.items.get().product_name, 'Morning mug')
        self.assertEqual(order.total, Decimal('498.00'))
        self.product.delete()
        self.assertEqual(order.items.get().product, None)
        self.assertEqual(order.total, Decimal('498.00'))

    def test_duplicate_order_is_idempotent_even_after_new_cart(self):
        self.add(2)
        data = self.checkout_data()
        self.client.post(reverse('checkout'), data)
        self.add(1)
        self.client.post(reverse('checkout'), data)
        self.assertEqual(Order.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(self.client.session['cart'][str(self.product.pk)], 1)

    def test_stock_change_rolls_back_and_keeps_cart(self):
        self.add(3)
        data = self.checkout_data()
        self.product.stock = 1
        self.product.save()
        response = self.client.post(reverse('checkout'), data)
        self.assertContains(response, 'insufficient stock')
        self.assertFalse(Order.objects.exists())
        self.assertFalse(OrderItem.objects.exists())
        self.assertEqual(self.client.session['cart'][str(self.product.pk)], 3)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)

    def test_entire_order_rolls_back_when_second_item_unavailable(self):
        second = Product.objects.create(category=self.category, name='Second', slug='second', price=25, stock=2)
        self.add(1)
        self.add(1, second)
        data = self.checkout_data()
        second.available = False
        second.save()
        self.client.post(reverse('checkout'), data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertFalse(Order.objects.exists())

    def test_deleted_product_blocks_checkout(self):
        self.add()
        data = self.checkout_data()
        self.product.delete()
        self.assertContains(self.client.post(reverse('checkout'), data), 'A product was removed')
        self.assertFalse(Order.objects.exists())

    def test_invalid_token_rejected(self):
        self.add()
        data = self.checkout_data()
        data['token'] = str(uuid.uuid4())
        self.assertContains(self.client.post(reverse('checkout'), data), 'checkout has expired')
        self.assertFalse(Order.objects.exists())

    def test_invalid_details_preserve_cart(self):
        self.add()
        data = self.checkout_data()
        data.update({'phone': '12', 'email': 'bad', 'name': ''})
        response = self.client.post(reverse('checkout'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())
        self.assertEqual(self.client.session['cart'][str(self.product.pk)], 1)

    def test_empty_checkout_redirect(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(reverse('checkout')), reverse('cart'))

    def test_order_access_is_owner_only(self):
        self.add()
        data = self.checkout_data()
        self.client.post(reverse('checkout'), data)
        order = Order.objects.get()
        self.assertContains(self.client.get(order.get_absolute_url()), order.number)
        self.assertContains(self.client.get(reverse('orders')), order.number)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse('orders')), order.number)
        self.client.logout()
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 302)

    def test_cart_removes_deleted_products(self):
        self.add()
        self.product.delete()
        response = self.client.get(reverse('cart'))
        self.assertContains(response, 'no longer sold')
        self.assertEqual(self.client.session['cart'], {})

    def test_last_item_cannot_be_sold_twice(self):
        self.product.stock = 1
        self.product.save()
        self.add()
        data = self.checkout_data()
        buyer_two = Client()
        buyer_two.force_login(self.other)
        buyer_two.post(reverse('add_cart', args=[self.product.pk]), {'quantity': 1})
        buyer_two.get(reverse('checkout'))
        other_data = dict(data, token=buyer_two.session['checkout_token'])
        self.client.post(reverse('checkout'), data)
        response = buyer_two.post(reverse('checkout'), other_data)
        self.assertContains(response, 'insufficient stock')
        self.assertEqual(Order.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)
        self.assertEqual(buyer_two.session['cart'][str(self.product.pk)], 1)

    def test_health_endpoint(self):
        self.assertJSONEqual(self.client.get(reverse('health')).content, {'status': 'ok'})

    def test_uploaded_image_is_served_without_debug_static_routes(self):
        import io
        import tempfile
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory, DEBUG=False):
            content = io.BytesIO()
            Image.new('RGB', (12, 12), 'green').save(content, format='PNG')
            self.product.image = SimpleUploadedFile('example.png', content.getvalue(), content_type='image/png')
            self.product.save()
            response = self.client.get(reverse('product_image', args=[self.product.pk]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'image/png')
            self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
            self.assertTrue(b''.join(response.streaming_content).startswith(b'\x89PNG'))
            response.close()
            self.product.available = False
            self.product.save()
            self.assertEqual(self.client.get(reverse('product_image', args=[self.product.pk])).status_code, 404)

    def test_missing_image_returns_404(self):
        self.assertEqual(self.client.get(reverse('product_image', args=[self.product.pk])).status_code, 404)

    def test_nonimage_upload_is_not_served(self):
        import tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            self.product.image = SimpleUploadedFile('example.html', b'<script>alert(1)</script>')
            self.product.save()
            self.assertEqual(self.client.get(reverse('product_image', args=[self.product.pk])).status_code, 404)

    def test_media_alias_rejects_arbitrary_paths(self):
        self.assertEqual(self.client.get('/media/../config/settings.py').status_code, 404)
        self.assertEqual(self.client.get('/media/products/not-a-product.png').status_code, 404)
