from .base import *  # noqa

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "hqlz1wij3y@#vpg!^9nt%5ehd*7(svq@3p*rr4x-26kf*slfdl"

ALLOWED_HOSTS = ["*"]  # Allow all hosts for development

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

WAGTAIL_CACHE = False

try:
    from .local import *  # noqa
except ImportError:
    pass
