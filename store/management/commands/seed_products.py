from django.core.management.base import BaseCommand
from store.models import Category, Product

PRODUCTS = [
    ('Home & living', 'home', 'The morning mug', 'morning-mug', 'A softer start to your morning.', 'A generously sized stoneware mug with a comfortable handle and a warm, speckled finish. Perfect for that first cup of coffee or your evening tea. Capacity: 350 ml. Dishwasher safe.', '249.00', 'mug'),
    ('On the go', 'lifestyle', 'The everyday bottle', 'everyday-bottle', 'Stay refreshed. Tread a little lighter.', 'A reusable insulated stainless steel bottle in a calming olive finish. Double-wall construction helps keep drinks hot or cold. Capacity: 500 ml. Hand wash recommended.', '349.00', 'bottle'),
    ('Desk essentials', 'desk', 'The little thoughts notebook', 'little-thoughts-notebook', 'For ideas worth keeping.', 'A cloth-bound notebook with 160 ruled pages of cream paper, an elastic closure and a ribbon bookmark. A5 size. An easy companion for your plans, lists and little thoughts.', '189.00', 'notebook'),
    ('Home & living', 'home', 'The sculptural vase', 'sculptural-vase', 'A quiet statement, with or without stems.', 'An earthy terracotta vase with a sculptural silhouette. Style with dried stems or let its form speak for itself. Height: 20 cm. For dried arrangements; use a liner for fresh flowers.', '429.00', 'vase'),
    ('Home & living', 'home', 'The slow mornings candle', 'slow-mornings-candle', 'A small ritual. A slower moment.', 'Cedar and fig scented candle in a reusable amber vessel. A cotton wick and plant-based wax create a gentle glow. Weight: 200 g. Never leave a burning candle unattended.', '279.00', 'candle'),
    ('On the go', 'lifestyle', 'The take-it-everywhere tote', 'everywhere-tote', 'Your daily carry, considered.', 'A roomy cotton canvas tote in soft sage with reinforced straps and an interior pocket. Folds flat for easy storage. Dimensions: 38 x 40 cm. Gentle cold wash.', '229.00', 'tote'),
    ('Home & living', 'home', 'The breakfast bowl', 'breakfast-bowl', 'For slow breakfasts and second helpings.', 'A stoneware bowl with a tactile glaze and a wide, welcoming shape. From morning oats to evening soup, a useful piece you will reach for daily. Diameter: 18 cm. Dishwasher safe.', '219.00', 'bowl'),
    ('Desk essentials', 'desk', 'The golden hour lamp', 'golden-hour-lamp', 'A warm glow for your favourite corner.', 'A compact desk lamp with a pleated fabric shade and warm brass-tone stem. Height: 35 cm. Uses one E14 LED bulb, not included. Supplied with a South African plug.', '799.00', 'lamp'),
    ('Home & living', 'home', 'The gathering tray', 'gathering-tray', 'A place for your little things.', 'A gently curved wooden tray for keys, jewellery or a quiet coffee moment. Natural grain gives each piece a distinct character. Diameter: 28 cm. Wipe clean with a damp cloth.', '329.00', 'tray'),
    ('Home & living', 'home', 'The soft landing towel', 'soft-landing-towel', 'A little softness, every day.', 'A textured cotton hand towel in muted sage, finished with a simple fringe. Dimensions: 45 x 70 cm. Machine washable at 30 degrees. Wash with similar colours.', '179.00', 'towel'),
    ('Desk essentials', 'desk', 'The daily note pen', 'daily-note-pen', 'Put a little thought on paper.', 'A refillable ballpoint pen with a comfortable matte body and brass-tone details. Smooth black ink for notes, sketches and everything in between. Includes one refill.', '129.00', 'pen'),
    ('Home & living', 'home', 'The windowsill planter', 'windowsill-planter', 'Bring a little outside in.', 'A stoneware planter with a warm neutral glaze, made for a sunny shelf or desk. Diameter: 14 cm. Includes a drainage hole and matching saucer. Plant not included.', '299.00', 'planter'),
]

class Command(BaseCommand):
    help = 'Load 12 sample products. Safe to rerun; existing products and stock are preserved.'
    def handle(self, *args, **options):
        created = 0
        for category_name, category_slug, name, slug, short, description, price, artwork in PRODUCTS:
            category, _ = Category.objects.get_or_create(slug=category_slug, defaults={'name': category_name})
            _, new = Product.objects.get_or_create(slug=slug, defaults={
                'category': category, 'name': name, 'short_description': short, 'description': description,
                'price': price, 'stock': 20, 'available': True, 'artwork': artwork,
            })
            created += new
        self.stdout.write(self.style.SUCCESS(f'Created {created} sample products. Existing products were preserved.'))
