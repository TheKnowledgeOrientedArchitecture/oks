#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django import forms

class ExploreOtherKSForm(forms.Form):
    ks_complete_url = forms.CharField(required=True, label="Full URL", help_text='<protocol><domain><port><path> try: http://licensedemo.thekoa.org')

