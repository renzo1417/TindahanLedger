"""Enable Row Level Security and revoke public Supabase API grants on all public tables."""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Enable RLS and revoke anon/authenticated/PUBLIC privileges on all public PostgreSQL tables.'

    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write('Skipping: database vendor is not PostgreSQL.')
            return

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
            )
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                quoted_table = connection.ops.quote_name(table)
                cursor.execute(f'ALTER TABLE public.{quoted_table} ENABLE ROW LEVEL SECURITY;')

            cursor.execute("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")
            roles = [row[0] for row in cursor.fetchall()]

            for role in roles:
                quoted_role = connection.ops.quote_name(role)
                cursor.execute(f'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {quoted_role};')
                cursor.execute(f'REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {quoted_role};')
                cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM {quoted_role};')
                cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM {quoted_role};')

            cursor.execute('REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;')
            cursor.execute('REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;')

        self.stdout.write(
            self.style.SUCCESS(
                f'Enabled RLS on {len(tables)} public tables and revoked public privileges for roles: {", ".join(roles + ["PUBLIC"])}.'
            )
        )
