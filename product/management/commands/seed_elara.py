from django.core.management.base import BaseCommand

from category.models import Category
from product.elara_seed import seed_elara
from product.models import Product, ProductImage, StorefrontSettings


class Command(BaseCommand):
    help = "Create the ELARA product page, or fill in its empty sections."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite title, price, size and every page section with the launch content.",
        )

    def handle(self, *args, force=False, **options):
        product, created = seed_elara(Product, ProductImage, Category, StorefrontSettings, force=force)
        action = "Created" if created else ("Reset" if force else "Filled empty sections of")
        self.stdout.write(self.style.SUCCESS(f"{action} product #{product.id} {product.title}"))
