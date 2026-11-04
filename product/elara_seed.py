"""Creates the ELARA product page. Used by a data migration and the seed_elara command.

Models are passed in so the migration can hand over its historical versions.
"""
from pathlib import Path

from django.core.files import File

from . import elara_content as content

SEED_DIR = Path(__file__).resolve().parent / "seed" / "elara"
LAUNCH_STOCK = 100


def _is_blank(value):
    return not value


def _save_image(field_file, name):
    if field_file:
        # Replacing, so don't leave the old upload behind
        field_file.delete(save=False)
    with open(SEED_DIR / name, "rb") as handle:
        field_file.save(name, File(handle), save=False)


def seed_elara(Product, ProductImage, Category, StorefrontSettings, force=False):
    """Create ELARA, or fill the empty page sections of an existing ELARA product.

    Without force, nothing an admin already filled in is changed, and price, stock and
    title of an existing product are left alone. Returns (product, created).
    """
    product = Product.objects.filter(title__icontains="elara").order_by("id").first()
    created = product is None

    if created:
        category = (
            Category.objects.filter(name__iexact=content.CATEGORY_NAME).first()
            or Category.objects.create(name=content.CATEGORY_NAME)
        )
        product = Product(category=category, stock=LAUNCH_STOCK, **content.PRODUCT)
    elif force:
        for field, value in content.PRODUCT.items():
            setattr(product, field, value)

    for field, value in content.CONTENT.items():
        if created or force or _is_blank(getattr(product, field)):
            setattr(product, field, value)

    translations = dict(product.translations or {})
    if created or force or not translations.get("ar"):
        translations["ar"] = content.ARABIC
    product.translations = translations

    for field in ("ingredients_image", "texture_image"):
        if created or force or not getattr(product, field):
            _save_image(getattr(product, field), content.IMAGES[field])

    product.save()

    if not ProductImage.objects.filter(product=product).exists():
        image = ProductImage(product=product)
        _save_image(image.image, content.IMAGES["hero"])
        image.save()

    settings_row, _ = StorefrontSettings.objects.get_or_create(pk=1)
    if settings_row.featured_product_id is None:
        settings_row.featured_product = product
        settings_row.save()

    return product, created
