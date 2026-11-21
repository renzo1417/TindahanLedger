"""Explicit administrator assignment with a dry run and no record deletion."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.home.models import Store, User


class Command(BaseCommand):
    help = 'Assign an unlinked legacy store to an existing login account. Dry run unless --apply is supplied.'

    def add_arguments(self, parser):
        parser.add_argument('--store', required=True, type=int)
        parser.add_argument('--username', required=True)
        parser.add_argument('--apply', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            account = get_user_model().objects.get(username=options['username'])
            owner = User.objects.get(auth_user=account)
            legacy = Store.objects.select_for_update().select_related('user').get(pk=options['store'])
        except (get_user_model().DoesNotExist, User.DoesNotExist, Store.DoesNotExist):
            raise CommandError('The login account, its business link, or the legacy store was not found.')
        if legacy.user_id == owner.pk:
            self.stdout.write('This account already owns the selected store. No records changed.')
            return
        if legacy.user.auth_user_id is not None:
            raise CommandError('This store already belongs to another login account. Assignment refused.')
        current = list(Store.objects.select_for_update().filter(user=owner))
        if len(current) > 1:
            raise CommandError('The target account has multiple stores. Review its ownership first.')
        if current:
            placeholder = current[0]
            if any(manager.exists() for manager in (placeholder.customers, placeholder.products, placeholder.categories,
                                                    placeholder.sales_transactions, placeholder.sms_reminders, placeholder.daily_summaries)):
                raise CommandError('The account’s existing store contains records. This command will not merge or replace them.')
            self.stdout.write(f'Empty store {placeholder.pk} will be retained under unlinked owner {legacy.user_id}.')
        self.stdout.write(f'Legacy store {legacy.pk} will belong to the supplied login account.')
        if not options['apply']:
            self.stdout.write('Dry run. Repeat with --apply to make this explicit assignment.')
            return
        if current:
            placeholder.user = legacy.user
            placeholder.save(update_fields=['user'])
        legacy.user = owner
        legacy.save(update_fields=['user'])
        self.stdout.write(self.style.SUCCESS('Store assigned. No stores or business records were deleted.'))
