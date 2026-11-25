from django import forms
from decimal import Decimal
from django.utils import timezone

from apps.user_settings.models import UserSettings
from .models import Customer, Product, Store


class CustomerForm(forms.ModelForm):
    initial_balance = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0, initial=0, label='Starting utang')
    initial_summary = forms.CharField(max_length=500, required=False, label='Opening balance note')

    class Meta:
        model = Customer
        fields = ['name', 'nickname', 'phone', 'address', 'credit_limit', 'notes']
        labels = {'name': 'Full name', 'phone': 'Phone number'}
        widgets = {'address': forms.Textarea(attrs={'rows': 2}), 'notes': forms.Textarea(attrs={'rows': 2})}

    def clean_credit_limit(self):
        value = self.cleaned_data['credit_limit']
        if value < 0:
            raise forms.ValidationError('Credit limit cannot be negative.')
        return value


class CustomerEditForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'nickname', 'phone', 'gcash', 'address', 'credit_limit', 'notes']
        labels = {'name': 'Full name', 'phone': 'Phone number', 'gcash': 'GCash number'}
        widgets = {'address': forms.Textarea(attrs={'rows': 2}), 'notes': forms.Textarea(attrs={'rows': 2})}

    def clean_credit_limit(self):
        value = self.cleaned_data['credit_limit']
        if value < 0:
            raise forms.ValidationError('Credit limit cannot be negative.')
        return value


class LedgerForm(forms.Form):
    customer_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    kind = forms.ChoiceField(choices=[('utang', 'Debt adjustment'), ('bayad', 'Payment')], widget=forms.HiddenInput)
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('.01'))
    summary = forms.CharField(max_length=1000, required=False, label='Description')
    due_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    payment_mode = forms.ChoiceField(choices=[('Cash', 'Cash'), ('GCash', 'GCash')], required=False)
    notes = forms.CharField(max_length=1000, required=False)


class ProductEditForm(forms.ModelForm):
    category_name = forms.CharField(max_length=100, required=False, label='Category')

    class Meta:
        model = Product
        fields = ['name', 'category_name', 'sku', 'unit', 'cost_price', 'selling_price', 'low_stock_threshold', 'has_expiry']
        labels = {'sku': 'SKU', 'has_expiry': 'Track expiry dates'}

    def clean(self):
        data = super().clean()
        for field in ('cost_price', 'selling_price', 'low_stock_threshold'):
            if data.get(field) is not None and data[field] < 0:
                self.add_error(field, 'This value cannot be negative.')
        if data.get('selling_price') == 0:
            self.add_error('selling_price', 'Enter a selling price greater than zero.')
        return data


class ProductCreateForm(ProductEditForm):
    stock_quantity = forms.IntegerField(min_value=0, max_value=1000000, initial=0, label='Opening stock')
    batch_code = forms.CharField(max_length=100, required=False, label='Batch code (optional)')
    expiry_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    shelf_location = forms.CharField(max_length=100, required=False)

    def clean(self):
        data = super().clean()
        if data.get('stock_quantity', 0) > 0 and data.get('has_expiry') and not data.get('expiry_date'):
            self.add_error('expiry_date', 'Enter the expiry date printed on the opening batch.')
        if data.get('expiry_date') and data['expiry_date'] < timezone.localdate():
            self.add_error('expiry_date', 'New stock cannot already be expired.')
        return data


class RestockForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=1000000)
    cost_price = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    selling_price = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('.01'))
    batch_code = forms.CharField(max_length=100, required=False)
    expiry_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    shelf_location = forms.CharField(max_length=100, required=False)


class ExpiryForm(forms.Form):
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))


class StoreProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = Store
        fields = ['store_name', 'owner_name', 'phone_number', 'gcash_number', 'email', 'address',
                  'city', 'business_category', 'operating_hours', 'ledger_volume']
        widgets = {'address': forms.Textarea(attrs={'rows': 2})}

    def clean_email(self):
        email = self.cleaned_data['email']
        from django.contrib.auth.models import User
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.user.auth_user_id).exists():
            raise forms.ValidationError('This email is already used by another account.')
        return email


class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['default_credit_limit', 'overdue_grace_days', 'reminder_threshold_days',
                  'expiry_window_days', 'low_stock_threshold', 'block_over_limit']
        labels = {'overdue_grace_days': 'Overdue grace period', 'reminder_threshold_days': 'Reminder threshold',
                  'expiry_window_days': 'Expiry warning window', 'low_stock_threshold': 'Default low stock threshold',
                  'block_over_limit': 'Block new credit over the limit'}
        help_texts = {
            'default_credit_limit': 'Used for new customers; existing limits stay unchanged.',
            'low_stock_threshold': 'Used for new products; existing thresholds stay unchanged.',
            'block_over_limit': 'Reject new credit entries that exceed a customer’s limit.',
        }

    def clean(self):
        data = super().clean()
        for field in self.Meta.fields[:-1]:
            if data.get(field) is not None and data[field] < 0:
                self.add_error(field, 'This value cannot be negative.')
        for field in ('overdue_grace_days', 'reminder_threshold_days', 'expiry_window_days'):
            if data.get(field, 0) > 365:
                self.add_error(field, 'Choose a value between 0 and 365 days.')
        return data
