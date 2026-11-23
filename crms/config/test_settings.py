"""Isolated SQLite tests: never use the configured store database."""
import os

os.environ['USE_LOCAL_DB'] = 'True'
from .settings import *  # noqa: F403, E402

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
