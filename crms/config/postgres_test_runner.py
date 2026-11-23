import os
import re
import psycopg
from psycopg import sql
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.test.runner import DiscoverRunner


class SchemaTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        schema = settings.TEST_SCHEMA
        if not re.fullmatch(r'ledger_test_[0-9a-f]{32}', schema):
            raise RuntimeError('Refusing an unsafe test schema name.')
        with psycopg.connect(os.environ['PG_TEST_DATABASE_URL'], sslmode='require', connect_timeout=10, autocommit=True) as conn:
            conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        self.created_schema = schema
        try:
            # Verify the server honored search_path before running any DDL. This
            # prevents a pooler that ignores startup options from using public.
            with connections['default'].cursor() as cursor:
                cursor.execute('SELECT current_schema(), current_schemas(false)')
                current, schemas = cursor.fetchone()
            if current != schema or schemas != [schema]:
                raise RuntimeError('Test connection is not isolated to its temporary schema.')
            call_command('migrate', verbosity=0, interactive=False)
        except Exception:
            self.teardown_databases([])
            raise
        return []

    def teardown_databases(self, old_config, **kwargs):
        schema = getattr(self, 'created_schema', None)
        if not schema or not re.fullmatch(r'ledger_test_[0-9a-f]{32}', schema):
            return
        connections.close_all()
        with psycopg.connect(os.environ['PG_TEST_DATABASE_URL'], sslmode='require', connect_timeout=10, autocommit=True) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
        self.created_schema = None
