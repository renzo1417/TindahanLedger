from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Sum
from apps.home.models import User, Store, Product, ProductBatch


class Command(BaseCommand):
    help = 'Read-only audit of account ownership, batch totals, and missing expiry dates.'

    def handle(self, *args, **options):
        products = Product.objects.annotate(batch_total=Sum('batches__quantity', filter=Q(batches__disposed_at__isnull=True)))
        mismatches = sum(p.stock_quantity != (p.batch_total or 0) for p in products)
        unlinked = User.objects.filter(auth_user__isnull=True).count()
        multiple = Store.objects.values('user_id').annotate(total=Count('pk')).filter(total__gt=1).count()
        missing = ProductBatch.objects.filter(product__has_expiry=True, expiry_date=None, disposed_at=None, quantity__gt=0).count()
        self.stdout.write(f'Unlinked legacy owners: {unlinked}')
        self.stdout.write(f'Owners with multiple stores: {multiple}')
        self.stdout.write(f'Product/batch quantity discrepancies: {mismatches}')
        self.stdout.write(f'Expiry-tracked batches needing dates: {missing}')
        self.stdout.write('Audit only. No records changed.')
