# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from django.test import TestCase
from knowledge_server.models import KnowledgeServer

class ThisKSTestCase(TestCase):
    def setUp(self):
        pass

    def test_this_ks_esists(self):
        thisKS = None
        try:
            thisKS = KnowledgeServer.this_knowledge_server()
        except:
            pass
        self.assertIsNotNone(thisKS)

