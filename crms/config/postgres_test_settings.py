"""PostgreSQL tests run in a disposable schema, never the public store tables."""
import os
from uuid import uuid4
import dj_database_url
from .settings import *  # noqa: F403

if not os.environ.get('PG_TEST_DATABASE_URL'):
    raise RuntimeError('Set PG_TEST_DATABASE_URL to run isolated PostgreSQL tests.')
TEST_SCHEMA = 'ledger_test_' + uuid4().hex
DATABASES = {'default': dj_database_url.parse(os.environ['PG_TEST_DATABASE_URL'], ssl_require=True)}
DATABASES['default']['OPTIONS'] = {'options': f'-c search_path={TEST_SCHEMA}', 'connect_timeout': 10}
TEST_RUNNER = 'config.postgres_test_runner.SchemaTestRunner'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
