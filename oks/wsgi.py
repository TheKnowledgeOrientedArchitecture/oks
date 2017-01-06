"""
WSGI config for oks project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import sys
import site

site.addsitedir('/root/py3env/lib/python3.4/site-packages')
site.addsitedir('/root/ks/beta/root/')

sys.path.append('/root/ks/beta/root/')
sys.path.append('/root/ks/beta/root/templates')
sys.path.append('/root/py3env/lib/python3.4/site-packages')


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oks.settings")

from django.core.wsgi import get_wsgi_application

import signal
try:
    application = get_wsgi_application()
except Exception:
    if 'mod_wsgi' in sys.modules:
        os.kill(os.getpid(), signal.SIGINT)
    raise
