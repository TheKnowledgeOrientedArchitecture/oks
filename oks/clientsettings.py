# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)


from oks.sharedsettings import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'dt3#g5g70qlv+^xn3jq#uz38n6%)d(jaqdxubbowa7)h#nb^*h'


INSTALLED_APPS += ('client',)


DATABASES['default']['NAME'] = 'betaclient'
DATABASES['materialized']['NAME'] = 'betaclientm'


LOGGING['handlers']['file']['filename'] = '/tmp/oks_client.log'
if not DEBUG:
    CACHES['default']['LOCATION'] = '/var/tmp/oks_cache/client_beta'
