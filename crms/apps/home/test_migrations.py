"""Regression for the legacy numeric-ID collision found in the local audit."""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class OwnershipMigrationTests(TransactionTestCase):
    def test_legacy_owner_is_not_replaced_by_unrelated_login_with_same_id(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        previous = [('home', '0001_initial'), ('user_settings', '0001_initial'),
                    ('auth', '0012_alter_user_first_name_max_length'), ('profile', '0001_initial')]
        executor.migrate(previous)
        try:
            old = executor.loader.project_state(previous).apps
            AuthUser = old.get_model('auth', 'User')
            Owner = old.get_model('home', 'User')
            Store = old.get_model('home', 'Store')
            Product = old.get_model('home', 'Product')
            Batch = old.get_model('home', 'ProductBatch')
            account = AuthUser.objects.create(username='real-login', password='unusable')
            legacy = Owner.objects.create(pk=account.pk, username='legacy-unclaimed', password_hash='legacy')
            store = Store.objects.create(user=legacy, store_name='Preserve this store', owner_name='Legacy owner')
            stock = Product.objects.create(store=store, name='Preserve this stock', stock_quantity=12)
            Batch.objects.create(product=stock, batch_code='Existing batch', quantity=9)
            matched_account = AuthUser.objects.create(username='username-match', password='unusable')
            matched_owner = Owner.objects.create(pk=matched_account.pk+100, username='username-match', password_hash='legacy')
            matched_store = Store.objects.create(user=matched_owner, store_name='Matched store', owner_name='Matched owner')
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            new = executor.loader.project_state(latest).apps
            NewOwner = new.get_model('home', 'User')
            NewStore = new.get_model('home', 'Store')
            self.assertIsNone(NewOwner.objects.get(pk=legacy.pk).auth_user_id)
            self.assertEqual(NewStore.objects.get(pk=store.pk).user_id, legacy.pk)
            self.assertNotEqual(NewOwner.objects.get(auth_user_id=account.pk).pk, legacy.pk)
            self.assertEqual(NewOwner.objects.get(pk=matched_owner.pk).auth_user_id, matched_account.pk)
            self.assertEqual(NewStore.objects.get(pk=matched_store.pk).user_id, matched_owner.pk)
            self.assertEqual(new.get_model('home', 'Product').objects.get(pk=stock.pk).stock_quantity, 9)
            self.assertEqual(new.get_model('home', 'ProductBatch').objects.filter(product_id=stock.pk).count(), 1)
            next_owner = NewOwner.objects.create(username='after-upgrade', password_hash='unusable')
            self.assertGreater(next_owner.pk, matched_owner.pk)
        finally:
            MigrationExecutor(connection).migrate(latest)
