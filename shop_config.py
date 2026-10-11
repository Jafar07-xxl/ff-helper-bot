"""Shop products and payment method labels shown by FF Helper."""

PRODUCTS = (
    {"id": "100", "category": "diamonds", "kind": "diamonds", "diamonds": 100, "price_tjs": "10"},
    {"id": "300", "category": "diamonds", "kind": "diamonds", "diamonds": 300, "price_tjs": "29"},
    {"id": "500", "category": "diamonds", "kind": "diamonds", "diamonds": 500, "price_tjs": "48"},
    {"id": "1000", "category": "diamonds", "kind": "diamonds", "diamonds": 1000, "price_tjs": "98"},
    {"id": "weekly_voucher", "category": "diamonds", "kind": "voucher", "diamonds": 0, "price_tjs": "18"},
    {"id": "monthly_voucher", "category": "diamonds", "kind": "voucher", "diamonds": 0, "price_tjs": "78"},
    {"id": "stars_50", "category": "stars", "kind": "telegram_stars", "diamonds": 0, "price_tjs": "15"},
    {"id": "stars_100", "category": "stars", "kind": "telegram_stars", "diamonds": 0, "price_tjs": "28"},
    {"id": "stars_250", "category": "stars", "kind": "telegram_stars", "diamonds": 0, "price_tjs": "65"},
    {"id": "stars_500", "category": "stars", "kind": "telegram_stars", "diamonds": 0, "price_tjs": "125"},
    {"id": "premium_1_month", "category": "premium", "kind": "telegram_premium", "diamonds": 0, "price_tjs": "45"},
    {"id": "premium_3_months", "category": "premium", "kind": "telegram_premium", "diamonds": 0, "price_tjs": "130"},
    {"id": "premium_12_months", "category": "premium", "kind": "telegram_premium", "diamonds": 0, "price_tjs": "400"},
)

PRODUCT_BY_ID = {product["id"]: product for product in PRODUCTS}
PRODUCTS_BY_CATEGORY = {
    category: tuple(product for product in PRODUCTS if product["category"] == category)
    for category in ("diamonds", "stars", "premium")
}
# Keep the previous names available for any local scripts that import them.
PACKAGES = PRODUCTS
PACKAGE_BY_ID = PRODUCT_BY_ID

PAYMENT_METHODS = {
    "alif": "Alif",
    "dushanbe_city": "Dushanbe City",
}
