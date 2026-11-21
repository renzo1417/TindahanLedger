"""Preserve unmatched legacy owners; link accounts only by exact username."""
from django.db import migrations
from django.core.management.color import no_style


def backfill(apps, schema_editor):
    alias = schema_editor.connection.alias
    AuthUser = apps.get_model('auth', 'User')
    User = apps.get_model('home', 'User')
    Store = apps.get_model('home', 'Store')
    Product = apps.get_model('home', 'Product')
    Batch = apps.get_model('home', 'ProductBatch')
    Settings = apps.get_model('user_settings', 'UserSettings')
    Profile = apps.get_model('profile', 'Profile')
    # The previous auth signal inserted business users with explicit auth IDs.
    # PostgreSQL does not advance the sequence for explicit IDs. Repair it before
    # provisioning any missing owners, so existing records cannot collide.
    with schema_editor.connection.cursor() as cursor:
        for statement in schema_editor.connection.ops.sequence_reset_sql(no_style(), [User]):
            cursor.execute(statement)
    for account in AuthUser.objects.using(alias).all().iterator():
        owner = User.objects.using(alias).filter(auth_user_id=account.pk).first()
        if owner is None:
            owner = User.objects.using(alias).filter(username=account.username, auth_user_id=None).first()
            if owner is None:
                owner = User.objects.using(alias).create(username=account.username, password_hash=account.password,
                    first_name=account.first_name, last_name=account.last_name, email=account.email, is_active=account.is_active,
                    date_joined=account.date_joined)
            owner.auth_user_id = account.pk
            owner.save(using=alias, update_fields=['auth_user'])
        owner_name = f'{account.first_name} {account.last_name}'.strip() or account.username
        Store.objects.using(alias).get_or_create(user_id=owner.pk, defaults={'store_name': f'{owner_name}’s Tindahan', 'owner_name': owner_name})
        Settings.objects.using(alias).get_or_create(user_id=account.pk)
        Profile.objects.using(alias).get_or_create(user_id=account.pk, defaults={'full_name': owner_name})
    for product in Product.objects.using(alias).all().iterator():
        batches = Batch.objects.using(alias).filter(product_id=product.pk)
        if not batches.exists() and product.stock_quantity > 0:
            Batch.objects.using(alias).create(product_id=product.pk, batch_code=f'OPENING-{product.pk}',
                quantity=product.stock_quantity, cost_price=product.cost_price, selling_price=product.selling_price)
        remaining = batches.filter(quantity__gt=0, disposed_at__isnull=True)
        quantity = sum(remaining.values_list('quantity', flat=True))
        status = 'out_of_stock' if quantity <= 0 else 'low_stock' if quantity <= product.low_stock_threshold else 'in_stock'
        Product.objects.using(alias).filter(pk=product.pk).update(stock_quantity=quantity, stock_status=status, active_batches_count=remaining.count())


class Migration(migrations.Migration):
    dependencies = [
        ('home', '0002_alter_category_options_alter_customer_options_and_more'),
        ('user_settings', '0002_usersettings_block_over_limit_and_more'),
        ('profile', '0001_initial'),
    ]
    # Account links and opening batches are deliberately retained on schema rollback.
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
