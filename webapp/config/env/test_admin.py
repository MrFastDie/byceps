from datetime import timedelta


DEBUG = False
PERMANENT_SESSION_LIFETIME = timedelta(14)
SECRET_KEY = b'\xcb;\xcd\xdc\x11\xf2\xa8\x08_Ks\xa3\xb0\xc5K/\x9b\xf1\xd9\xdc_\x16\x8e\xa8'
SERVER_NAME = 'example.com'
SESSION_COOKIE_SECURE = True
TESTING = True

LOCALE = 'de_DE.UTF-8'
LOCALES_FORMS = ['de']

SQLALCHEMY_DATABASE_URI = 'postgresql+pg8000://byceps_test:test@127.0.0.1/byceps_test'
SQLALCHEMY_ECHO = False

REDIS_URL = 'redis://127.0.0.1:6379/0'

MODE = 'admin'

MAIL_DEBUG = False
MAIL_DEFAULT_SENDER = 'LANresort <noreply@lanresort.de>'
MAIL_SUPPRESS_SEND = True

JOBS_ASYNC = False
