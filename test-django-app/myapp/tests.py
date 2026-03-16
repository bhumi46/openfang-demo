from django.test import TestCase
from myapp.models import Product


class ProductTestCase(TestCase):
    def test_product_str(self):
        product = Product(name="Widget", price=9.99)
        self.assertEqual(str(product), "Widget - $9.99")

    def test_discounted_price(self):
        """Test that a percentage discount is applied correctly."""
        product = Product(name="Widget", price=100.0)
        # discounted_price method does not exist yet — this will fail
        self.assertEqual(product.discounted_price(10), 90.0)
