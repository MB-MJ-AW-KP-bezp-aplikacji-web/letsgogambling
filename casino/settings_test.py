"""
Test settings for CI environment.
Uses SQLite in-memory for fast, isolated testing without external dependencies.
"""
from casino.settings import *  # noqa: F401, F403

# Use SQLite in-memory for testing (faster, no external services needed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable password validation for faster test execution
AUTH_PASSWORD_VALIDATORS = []

# Use in-memory channel layer for tests (no Redis needed)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Set required environment variables for testing
SECRET_KEY = 'test-secret-key-for-ci-testing-only'  # noqa

# Disable debug for more realistic testing
DEBUG = False

# Simplify static files handling for tests
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}
