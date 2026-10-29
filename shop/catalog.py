from product.models import Product


def _discounted_price(product):
    price = product.price or 0
    if product.discount and product.discount > 0:
        price = price - (price * product.discount / 100)
    return float(price)


def build_product_catalog(base_url=""):
    """
    Serialize the real Product table into the plain dicts the AI engine expects.
    `base_url` (e.g. "https://api.glowmi.net") is prefixed to relative media URLs.
    """
    catalog = []
    products = Product.objects.select_related("category").prefetch_related("images").order_by("id")
    for p in products:
        image_url = ""
        first_image = next((img for img in p.images.all() if img.image), None)
        if first_image:
            image_url = f"{base_url}{first_image.image.url}"

        catalog.append({
            "id": p.id,
            "name": p.title,
            "category": p.category.name if p.category else "Skincare",
            "sub_title": p.sub_title or "",
            "skin_type": p.skin_type or "",
            "ingredients": p.key_ingredients or "",
            "benefits": p.key_benefits or "",
            "description": (p.description or "")[:400],
            "how_to_use": p.how_to_use or "",
            "size": p.size or "",
            "price": _discounted_price(p),
            "in_stock": (p.stock or 0) > 0,
            "image_url": image_url,
            "product_url": f"/products/{p.id}",
        })
    return catalog


def get_catalog_product(catalog, product_id):
    for product in catalog:
        if product["id"] == product_id:
            return product
    return None
