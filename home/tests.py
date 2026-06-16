from django.test import TestCase
from django.conf import settings
from home.models import RestaurantLocation, Category, MenuItem, Addon, OrderItem, OrderItemAddon
from home.context_processors import site_meta


class HomeTests(TestCase):
    def test_index_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_site_meta_fallback_to_settings(self):
        # Clean up locations
        RestaurantLocation.objects.all().delete()
        meta = site_meta(None)
        self.assertEqual(meta["restaurant_name"], getattr(settings, "RESTAURANT_NAME", "Foodora Kitchen"))
        self.assertEqual(meta["restaurant_address"], getattr(settings, "RESTAURANT_ADDRESS", ""))

    def test_site_meta_loads_active_location(self):
        # Create an active location with blank map_embed_url
        loc = RestaurantLocation.objects.create(
            name="Test Branch",
            address="123 Test Street",
            phone="9999999999",
            is_active=True,
            is_primary=False
        )
        meta = site_meta(None)
        self.assertEqual(meta["restaurant_name"], "Test Branch")
        self.assertEqual(meta["restaurant_address"], "123 Test Street")
        self.assertEqual(meta["restaurant_phone"], "9999999999")
        # Should generate fallback embed URL
        self.assertEqual(meta["restaurant_map_embed_url"], "https://maps.google.com/maps?q=Test%20Branch%20123%20Test%20Street&output=embed")

    def test_site_meta_uses_provided_map_embed_url(self):
        loc = RestaurantLocation.objects.create(
            name="Test Branch 2",
            address="456 Test Street",
            map_embed_url="https://custom-embed-url.com",
            is_active=True,
            is_primary=True
        )
        meta = site_meta(None)
        # Should use the provided map_embed_url
        self.assertEqual(meta["restaurant_map_embed_url"], "https://custom-embed-url.com")

    def test_site_meta_prioritizes_primary_location(self):
        # Create a standard active location
        RestaurantLocation.objects.create(
            name="Standard Branch",
            address="456 Standard Ave",
            is_active=True,
            is_primary=False,
            ordering=1
        )
        # Create a primary active location
        RestaurantLocation.objects.create(
            name="Primary Branch",
            address="789 Primary Blvd",
            is_active=True,
            is_primary=True,
            ordering=2
        )
        meta = site_meta(None)
        self.assertEqual(meta["restaurant_name"], "Primary Branch")
        self.assertEqual(meta["restaurant_address"], "789 Primary Blvd")


class AddonTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Burgers", slug="burgers")
        self.item = MenuItem.objects.create(
            category=self.category,
            name="Classic Burger",
            slug="classic-burger",
            price=150.00,
            is_available=True,
            stock_qty=10
        )
        self.addon_cheese = Addon.objects.create(
            menu_item=self.item,
            name="Extra Cheese",
            price=30.00,
            is_active=True
        )
        self.addon_sauce = Addon.objects.create(
            menu_item=self.item,
            name="Extra Sauce",
            price=15.00,
            is_active=True
        )
        self.addon_inactive = Addon.objects.create(
            menu_item=self.item,
            name="Gold Leaf",
            price=500.00,
            is_active=False
        )

    def test_menu_item_addon_helpers(self):
        # has_addons should be True because of active addons
        self.assertTrue(self.item.has_addons)
        
        # active_addons_json should serialize only active addons
        import json
        addons = json.loads(self.item.active_addons_json)
        self.assertEqual(len(addons), 2)
        addon_names = [a["name"] for a in addons]
        self.assertIn("Extra Cheese", addon_names)
        self.assertIn("Extra Sauce", addon_names)
        self.assertNotIn("Gold Leaf", addon_names)

    def test_cart_addons_pricing(self):
        session = self.client.session
        session["cart"] = {
            "item_with_addons": {
                "menu_item_id": self.item.id,
                "quantity": 2,
                "spice_level": "MEDIUM",
                "addon_ids": [str(self.addon_cheese.id), str(self.addon_sauce.id)]
            }
        }
        session.save()

        # Parse cart and check row unit price and line total
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.session = session
        
        from home.context_processors import cart_context
        ctx = cart_context(request)
        
        # Total price should be (150.00 + 30.00 + 15.00) * 2 = 195.00 * 2 = 390.00
        self.assertEqual(ctx["cart_total"], 390.00)
        
        cart_rows = ctx["cart_items"]
        self.assertEqual(len(cart_rows), 1)
        row = cart_rows[0]
        self.assertEqual(row.unit_price, 195.00)
        self.assertEqual(row.line_total, 390.00)
        self.assertEqual(len(row.addons), 2)

    def test_order_creation_with_addons(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username="testuser", email="test@test.com", password="password")
        from home.models import Address
        address = Address.objects.create(
            user=user,
            full_name="Test Recipient",
            phone="1234567890",
            line1="123 Test Street",
            city="Test City",
            state="Test State",
            pincode="12345"
        )
        
        session = self.client.session
        session["cart"] = {
            "item_with_addons": {
                "menu_item_id": self.item.id,
                "quantity": 1,
                "spice_level": "MILD",
                "addon_ids": [str(self.addon_cheese.id)]
            }
        }
        session["checkout_address_id"] = address.id
        session.save()

        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/')
        request.user = user
        request.session = session

        from home.views import build_order_from_cart
        order = build_order_from_cart(request)
        
        self.assertIsNotNone(order)
        order_items = order.items.all()
        self.assertEqual(len(order_items), 1)
        it = order_items[0]
        
        # Unit price should be (150.00 + 30.00) = 180.00
        self.assertEqual(it.unit_price, 180.00)
        
        # OrderItemAddon should be created
        item_addons = it.addons.all()
        self.assertEqual(len(item_addons), 1)
        ia = item_addons[0]
        self.assertEqual(ia.name, "Extra Cheese")
        self.assertEqual(ia.price, 30.00)


class GuestLoginTests(TestCase):
    def test_guest_login_creates_user_and_logs_in(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        initial_count = User.objects.count()
        
        response = self.client.post("/accounts/guest/", {"next": "/orders/checkout/address/"})
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/orders/checkout/address/"))
        
        self.assertEqual(User.objects.count(), initial_count + 1)
        guest_user = User.objects.order_by("-id").first()
        self.assertTrue(guest_user.email.startswith("guest_"))
        self.assertTrue(guest_user.email.endswith("@foodora.com"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), guest_user.id)


class FulfillmentCheckoutTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username="testcheckout@test.com", email="testcheckout@test.com", password="password")
        self.client.force_login(self.user)
        
        self.category = Category.objects.create(name="Pizza", slug="pizza")
        self.item = MenuItem.objects.create(
            category=self.category,
            name="Margherita",
            slug="margherita",
            price=250.00,
            is_available=True,
            stock_qty=10
        )
        
        RestaurantLocation.objects.create(
            name="Main Headquarters",
            address="456 Main St, City, State",
            is_active=True,
            is_primary=True
        )

    def test_delivery_checkout_requires_address_fields(self):
        session = self.client.session
        session["cart"] = {
            "item_key": {
                "menu_item_id": self.item.id,
                "quantity": 1,
                "spice_level": "MILD",
                "addon_ids": []
            }
        }
        session["order_type"] = "DELIVERY"
        session.save()
        
        response = self.client.post("/orders/checkout/address/", {
            "full_name": "Test User",
            "phone": "9999999999"
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], None, "Choose a saved address or complete all address fields.")

    def test_pickup_checkout_requires_only_name_and_phone(self):
        session = self.client.session
        session["cart"] = {
            "item_key": {
                "menu_item_id": self.item.id,
                "quantity": 1,
                "spice_level": "MILD",
                "addon_ids": []
            }
        }
        session["order_type"] = "PICKUP"
        session.save()
        
        response = self.client.post("/orders/checkout/address/", {
            "full_name": "Test Guest User",
            "phone": "9999999999"
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/orders/checkout/confirm/"))
        
        from home.models import Address
        addr = Address.objects.filter(user=self.user).first()
        self.assertIsNotNone(addr)
        self.assertEqual(addr.full_name, "Test Guest User")
        self.assertEqual(addr.phone, "9999999999")
        self.assertEqual(addr.line1, "Pickup from: Main Headquarters")
        self.assertEqual(addr.line2, "456 Main St, City, State")


class HeroSelectionTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Burgers", slug="burgers")
        self.item1 = MenuItem.objects.create(
            category=self.category,
            name="Burger 1",
            slug="burger-1",
            price=150.00,
            is_available=True,
            stock_qty=10,
            is_hero=False
        )
        self.item2 = MenuItem.objects.create(
            category=self.category,
            name="Burger 2",
            slug="burger-2",
            price=180.00,
            is_available=True,
            stock_qty=10,
            is_hero=False
        )

    def test_single_hero_item_enforcement(self):
        self.item1.is_hero = True
        self.item1.save()
        
        self.assertTrue(MenuItem.objects.get(pk=self.item1.pk).is_hero)
        self.assertFalse(MenuItem.objects.get(pk=self.item2.pk).is_hero)
        
        self.item2.is_hero = True
        self.item2.save()
        
        self.assertFalse(MenuItem.objects.get(pk=self.item1.pk).is_hero)
        self.assertTrue(MenuItem.objects.get(pk=self.item2.pk).is_hero)

    def test_home_page_displays_hero_item(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["hero_item"].name, "Burger 1")
        
        self.item2.is_hero = True
        self.item2.save()
        
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["hero_item"].name, "Burger 2")




