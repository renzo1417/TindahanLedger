from django.contrib import admin
from .models import (
    User,
    Store,
    Category,
    Product,
    ProductBatch,
    Customer,
    SalesTransaction,
    SalesTransactionItem,
    CustomerLedgerTransaction,
    SMSReminder,
    DailyStoreSummary,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'auth_user', 'email', 'phone', 'first_name', 'last_name', 'is_active', 'date_joined')
    readonly_fields = ('password_hash',)
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    list_filter = ('is_active', 'date_joined')


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'store_name', 'owner_name', 'phone_number', 'gcash_number', 'is_device_synced', 'created_at')
    search_fields = ('store_name', 'owner_name', 'phone_number')
    list_filter = ('is_device_synced', 'created_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'store', 'slug', 'created_at')
    search_fields = ('name', 'store__store_name')
    prepopulated_fields = {'slug': ('name',)}


class ProductBatchInline(admin.TabularInline):
    model = ProductBatch
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'store', 'category', 'selling_price', 'cost_price', 'profit_margin', 'stock_quantity', 'stock_status')
    search_fields = ('name', 'sku', 'store__store_name')
    list_filter = ('stock_status', 'has_expiry', 'category')
    inlines = [ProductBatchInline]


@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch_code', 'product', 'quantity', 'expiry_date', 'status', 'days_left', 'capital_loss')
    search_fields = ('batch_code', 'product__name')
    list_filter = ('status', 'expiry_date')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'nickname', 'store', 'phone', 'credit_limit', 'running_balance', 'status', 'days_overdue', 'due_date')
    search_fields = ('name', 'nickname', 'phone', 'store__store_name')
    list_filter = ('status', 'due_date')


class SalesTransactionItemInline(admin.TabularInline):
    model = SalesTransactionItem
    extra = 1


@admin.register(SalesTransaction)
class SalesTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'receipt_no', 'store', 'customer', 'payment_method', 'total_amount', 'profit_earned', 'transaction_date')
    search_fields = ('receipt_no', 'store__store_name', 'customer__name')
    list_filter = ('payment_method', 'transaction_type', 'transaction_date')
    inlines = [SalesTransactionItemInline]


@admin.register(SalesTransactionItem)
class SalesTransactionItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction', 'product', 'batch', 'quantity', 'unit_price', 'subtotal_amount', 'profit_amount')
    search_fields = ('transaction__receipt_no', 'product__name')


@admin.register(CustomerLedgerTransaction)
class CustomerLedgerTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'reference_no', 'customer', 'transaction_type', 'amount', 'running_balance', 'payment_mode', 'transaction_date')
    search_fields = ('reference_no', 'customer__name')
    list_filter = ('transaction_type', 'payment_mode', 'transaction_date')


@admin.register(SMSReminder)
class SMSReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'store', 'phone_number', 'tone', 'balance_at_send', 'sent_status', 'sent_at')
    search_fields = ('customer__name', 'phone_number')
    list_filter = ('sent_status', 'tone')


@admin.register(DailyStoreSummary)
class DailyStoreSummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'store', 'report_date', 'gross_sales', 'gross_margin', 'margin_pct', 'cash_collected', 'uncollected_utang', 'transactions_count')
    search_fields = ('store__store_name',)
    list_filter = ('report_date',)
