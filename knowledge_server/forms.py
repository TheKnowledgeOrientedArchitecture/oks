#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from django import forms

class ExploreOtherKSForm(forms.Form):
    ks_complete_url = forms.CharField(required=True, label="Full URL", help_text='<protocol><domain><port><path> try: http://licensedemo.thekoa.org')

