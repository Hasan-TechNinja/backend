from django.db import migrations

from product.elara_seed import seed_elara


def create_elara(apps, schema_editor):
    seed_elara(
        apps.get_model("product", "Product"),
        apps.get_model("product", "ProductImage"),
        apps.get_model("category", "Category"),
        apps.get_model("product", "StorefrontSettings"),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("category", "0005_remove_category_description_alter_category_name"),
        ("product", "0008_product_page_sections"),
    ]

    operations = [
        migrations.RunPython(create_elara, migrations.RunPython.noop),
    ]
