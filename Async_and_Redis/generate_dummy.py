import os
import django
import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User
from market.models import Product, Order, OrderItem, APILog


# -------------------------------------------------
# 설정 (데이터 양 조절 가능)
# -------------------------------------------------
USER_COUNT = 200
PRODUCT_COUNT = 2000
ORDER_COUNT = 10000
API_LOG_COUNT = 50000


def create_users():
    print("👤 Creating Users...")
    users = [
        User(
            username = f"user{i}",
            email = f"user{i}@test.com"
        )
        for i in range(USER_COUNT)
    ]
    User.objects.bulk_create(users, ignore_conflicts=True)
    print(f"✅ {USER_COUNT} users created")


#####################


def create_products():
    print("📦 Creating Products...")
    categories = ["electronics", "books", "fashion", "food", "sports"]

    products = [
        Product(
            name=f"Product {i}",
            description="Performance testing product",
            price=Decimal(random.randint(10, 1000)),
            stock=random.randint(0, 500),
            category=random.choice(categories)
        )
        for i in range(PRODUCT_COUNT)
    ]

    Product.objects.bulk_create(products, batch_size=1000)
    print(f"✅ {PRODUCT_COUNT} products created")


#####################


def create_orders():
    print("🧾 Creating Orders...")
    users = list(User.objects.all())
    now = timezone.now()

    orders = [
        Order(
            user = random.choice(users),
            total_amount = Decimal(random.randint(50, 500)),
            status = random.choice(["pending", "processing", "completed"]),
            created_at = now - timedelta(days=random.randint(0, 30))
        )
        
        for _ in range(ORDER_COUNT)
    ]

    Order.objects.bulk_create(orders, batch_size=1000)
    print(f"✅ {ORDER_COUNT} orders created")


#####################


def create_order_items():
    print("🛒 Creating OrderItems (N+1 유도용)...")

    orders = list(Order.objects.all())
    products = list(Product.objects.all())

    items = []

    for order in orders:
        for _ in range(random.randint(1, 5)):  # 주문당 1~5개 상품
            product = random.choice(products)

            items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=random.randint(1, 3),
                    price=product.price
                )
            )

    OrderItem.objects.bulk_create(items, batch_size=2000)
    print(f"✅ {len(items)} order items created")


#####################


def create_api_logs():
    print("📡 Creating API Logs (Index 테스트용)...")

    now = timezone.now()

    logs = [
        APILog(
            endpoint = "/api/orders",
            method = "GET",
            status_code = random.choice([200, 200, 200, 500]),
            response_time = random.random() * 2,
            created_at = now - timedelta(minutes=random.randint(0, 10000))
        )
        for _ in range(API_LOG_COUNT)
    ]

    APILog.objects.bulk_create(logs, batch_size=2000)
    print(f"✅ {API_LOG_COUNT} api logs created")


#####################


if __name__ == "__main__":
    create_users()
    create_products()
    create_orders()
    create_order_items()
    create_api_logs()

    print("\n🎯 Dummy Data Generation Complete!")
