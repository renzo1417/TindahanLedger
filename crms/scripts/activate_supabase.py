"""Verify/migrate Supabase before changing the local database selection.

Run from the repository root with the project virtual environment.
Connection details are read from crms/.env and are never printed.
"""
import os
from pathlib import Path
import sys

from dotenv import load_dotenv, set_key

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
load_dotenv(BASE / '.env', override=True)
os.environ['USE_LOCAL_DB'] = 'False'
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'


def main():
    if not os.environ.get('DATABASE_URL'):
        raise SystemExit('Set DATABASE_URL in crms/.env first.')
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connection, DatabaseError
    from django.db.migrations.executor import MigrationExecutor
    try:
        if connection.vendor != 'postgresql':
            raise SystemExit('DATABASE_URL must select PostgreSQL.')
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        executor = MigrationExecutor(connection)
        executor.loader.check_consistent_history(connection)
        tables = set(connection.introspection.table_names())
        if 'stores' in tables and 'django_migrations' not in tables:
            raise SystemExit('Existing store tables have no Django migration history. Review the schema before migration; the database selection was not changed.')
        call_command('migrate', interactive=False)
        call_command('check')
        call_command('audit_store_data')
    except DatabaseError:
        raise SystemExit('Supabase could not complete verification/migration. Check the current project, database user, and password in crms/.env. The database selection was not changed.') from None
    set_key(BASE / '.env', 'USE_LOCAL_DB', 'False')
    print('Supabase verified and migrated. USE_LOCAL_DB=False is now saved in crms/.env.')


if __name__ == '__main__':
    main()
