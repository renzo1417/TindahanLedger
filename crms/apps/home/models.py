from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User as AuthUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal


# 1. users
class User(models.Model):
    auth_user = models.OneToOneField(AuthUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='business_user')
    username = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=255)
    email = models.CharField(max_length=254, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


# 2. stores
class Store(models.Model):
    is_demo = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stores', db_column='user_id')
    store_name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    gcash_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    business_category = models.CharField(max_length=150, blank=True)
    city = models.CharField(max_length=150, blank=True)
    operating_hours = models.CharField(max_length=150, blank=True)
    ledger_volume = models.CharField(max_length=100, blank=True)
    is_device_synced = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stores'
        verbose_name = 'Store'
        verbose_name_plural = 'Stores'

    def __str__(self):
        return self.store_name


# 3. categories
class Category(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='categories', db_column='store_id')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


# 4. products
class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products', db_column='store_id')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', db_column='category_id')
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, default='pc')
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    profit_margin = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    profit_margin_pct = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    stock_status = models.CharField(max_length=50, default='in_stock')
    has_expiry = models.BooleanField(default=False)
    active_batches_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def save(self, *args, **kwargs):
        if self.selling_price is not None and self.cost_price is not None:
            self.profit_margin = self.selling_price - self.cost_price
            self.profit_margin_pct = round((self.profit_margin / self.cost_price) * Decimal('100.00'), 2) if self.cost_price > 0 else Decimal('0.00')
        if self.stock_quantity <= 0:
            self.stock_status = 'out_of_stock'
        elif self.stock_quantity <= self.low_stock_threshold:
            self.stock_status = 'low_stock'
        else:
            self.stock_status = 'in_stock'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# 5. product_batches
class ProductBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches', db_column='product_id')
    batch_code = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, default='healthy')
    status_label = models.CharField(max_length=100, blank=True)
    days_left = models.IntegerField(null=True, blank=True)
    capital_loss = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shelf_location = models.CharField(max_length=100, blank=True)
    disposed_at = models.DateTimeField(null=True, blank=True)
    disposed_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_batches'
        verbose_name = 'Product Batch'
        verbose_name_plural = 'Product Batches'

    def save(self, *args, **kwargs):
        if self.expiry_date:
            today = timezone.localdate()
            delta = (self.expiry_date - today).days
            self.days_left = delta
            if delta < 0:
                self.status, self.status_label = 'expired', f"Expired {abs(delta)} days ago"
            elif delta <= 7:
                self.status, self.status_label = 'expiring_soon', f"Expires in {delta} days"
            else:
                self.status, self.status_label = 'healthy', f"Fresh ({delta} days left)"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} [{self.batch_code}]"


# 6. customers
class Customer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='customers', db_column='store_id')
    name = models.CharField(max_length=150)
    nickname = models.CharField(max_length=100, blank=True)
    avatar_letter = models.CharField(max_length=5, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    gcash = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    running_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=50, default='active')
    status_label = models.CharField(max_length=100, blank=True)
    due_date = models.DateField(null=True, blank=True)
    last_payment_date = models.DateField(null=True, blank=True)
    days_overdue = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

    def save(self, *args, **kwargs):
        if not self.avatar_letter and self.name:
            self.avatar_letter = self.name.strip()[0].upper()
        if self.due_date and self.running_balance > Decimal('0.00'):
            today = timezone.localdate()
            if today > self.due_date:
                self.days_overdue = (today - self.due_date).days
                self.status, self.status_label = 'overdue', f"{self.days_overdue} days overdue"
            else:
                self.days_overdue, self.status, self.status_label = 0, 'active', 'Active Utang'
        elif self.running_balance <= Decimal('0.00'):
            self.days_overdue, self.status, self.status_label = 0, 'settled', 'Settled / No Utang'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.nickname})" if self.nickname else self.name


# 7. sales_transactions
class SalesTransaction(models.Model):
    checkout_token = models.UUIDField(null=True, blank=True, unique=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='sales_transactions', db_column='store_id')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_transactions', db_column='customer_id')
    receipt_no = models.CharField(max_length=100, unique=True)
    transaction_type = models.CharField(max_length=50, default='sale')
    payment_method = models.CharField(max_length=50, default='Cash')
    items_count = models.IntegerField(default=0)
    items_summary = models.TextField(blank=True)
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    cash_tendered = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    change_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    profit_earned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    transaction_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sales_transactions'
        verbose_name = 'Sales Transaction'
        verbose_name_plural = 'Sales Transactions'

    def __str__(self):
        return f"#{self.receipt_no} (₱{self.total_amount})"


# 8. sales_transaction_items
class SalesTransactionItem(models.Model):
    transaction = models.ForeignKey(SalesTransaction, on_delete=models.CASCADE, related_name='items', db_column='transaction_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales_items', db_column='product_id')
    batch = models.ForeignKey(ProductBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_items', db_column='batch_id')
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    profit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sales_transaction_items'
        verbose_name = 'Sales Transaction Item'
        verbose_name_plural = 'Sales Transaction Items'

    def save(self, *args, **kwargs):
        self.subtotal_amount = (self.unit_price or Decimal('0.00')) * self.quantity
        self.profit_amount = self.subtotal_amount - ((self.cost_price or Decimal('0.00')) * self.quantity)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


# 9. customer_ledger_transactions
class CustomerLedgerTransaction(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='ledger_transactions', db_column='customer_id')
    sales_transaction = models.ForeignKey(SalesTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries', db_column='sales_transaction_id')
    reference_no = models.CharField(max_length=100)
    transaction_type = models.CharField(max_length=50)
    type_label = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    running_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payment_mode = models.CharField(max_length=50, blank=True)
    items_summary = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    transaction_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customer_ledger_transactions'
        verbose_name = 'Customer Ledger Transaction'
        verbose_name_plural = 'Customer Ledger Transactions'

    def __str__(self):
        return f"{self.customer.name} - {self.transaction_type}: {self.amount}"


# 10. sms_reminders
class SMSReminder(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sms_reminders', db_column='customer_id')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='sms_reminders', db_column='store_id')
    tone = models.CharField(max_length=50, default='friendly')
    phone_number = models.CharField(max_length=20)
    message_content = models.TextField()
    balance_at_send = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    sent_status = models.CharField(max_length=50, default='simulated')
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sms_reminders'
        verbose_name = 'SMS Reminder'
        verbose_name_plural = 'SMS Reminders'

    def __str__(self):
        return f"SMS to {self.phone_number} ({self.sent_status})"


# 11. daily_store_summaries
class DailyStoreSummary(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='daily_summaries', db_column='store_id')
    report_date = models.DateField()
    gross_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    gross_margin = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    margin_pct = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    cash_collected = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    uncollected_utang = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    transactions_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_store_summaries'
        verbose_name = 'Daily Store Summary'
        verbose_name_plural = 'Daily Store Summaries'
        unique_together = ('store', 'report_date')

    def __str__(self):
        return f"{self.store.store_name} - {self.report_date}"


# Signals for Auth Sync
@receiver(post_save, sender=AuthUser)
def sync_auth_user_with_erd(sender, instance, created, **kwargs):
    if kwargs.get('raw'):
        return
    linked = User.objects.filter(auth_user=instance).first()
    username = instance.username
    if User.objects.filter(username=username).exclude(pk=linked.pk if linked else None).exists():
        username = f'account-{instance.pk}-{instance.username}'[:150]
    erd_user, _ = User.objects.update_or_create(
        auth_user=instance,
        defaults={
            'username': username,
            'password_hash': instance.password,
            'email': instance.email or '',
            'phone': instance.username if instance.username.replace('+', '').isdigit() else '',
            'first_name': instance.first_name or '',
            'last_name': instance.last_name or '',
            'is_active': instance.is_active,
            'date_joined': instance.date_joined,
        }
    )
    if created:
        owner_name = f"{instance.first_name} {instance.last_name}".strip() or instance.username
        Store.objects.get_or_create(
            user=erd_user,
            defaults={
                'store_name': f"{owner_name}'s Tindahan",
                'owner_name': owner_name,
                'phone_number': erd_user.phone or '',
                'is_device_synced': False,
            }
        )
