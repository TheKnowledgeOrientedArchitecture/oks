# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it
import json
import urllib

from django import template
from django.core.urlresolvers import reverse
from knowledge_server.models import KnowledgeServer 
register = template.Library()

@register.simple_tag
def ks_info(ks, *args, **kwargs):
    ret_html = "<p>" + ks.name
    if hasattr(ks, "organization"):
        ret_html += '<br>Maintained by "<a href="' + ks.organization.website + '" target="_blank">' + ks.organization.name + '</a>"'
    ret_html += '<br><a href="' + ks.url() + '/" target="_blank">' + ks.url() + '</a>'
    
    return ret_html

@register.simple_tag
def version_instance_info(dataset, instances, *args, **kwargs):
    DataSet_UKCL = urllib.parse.quote(dataset.UKCL).replace("/","%2F")
    ret_string = ''
    for instance in instances:
        html_url = reverse('api_dataset_view', args=(DataSet_UKCL,instance.pk,"html")) if dataset.dataset_structure.is_a_view else reverse('api_dataset', args=(DataSet_UKCL,"html"))
        xml_url = reverse('api_dataset_view', args=(DataSet_UKCL,instance.pk,"XML")) if dataset.dataset_structure.is_a_view else reverse('api_dataset', args=(DataSet_UKCL,"XML"))
        json_url = reverse('api_dataset_view', args=(DataSet_UKCL,instance.pk,"JSON")) if dataset.dataset_structure.is_a_view else reverse('api_dataset', args=(DataSet_UKCL,"JSON"))
        ret_string +=  '<p>"' + instance.name + '" (<a href="' + html_url + '">browse the data</a> or'
        ret_string += ' get it in <a href="' + xml_url + '">XML</a> or '
        ret_string += '<a href="' + json_url + '">JSON</a>)<br>'
        if not dataset.dataset_structure.is_a_view:
            ret_string += 'Version ' + ('<strong>' if dataset.version_released else '(<font color="red">not released</font>) ') + str(dataset.version_major) + '.' + str(dataset.version_minor) + '.' + str(dataset.version_patch) + '</strong> - ' + str(dataset.version_date)
        if not dataset.licenses is None:
            ret_string += '<br>Licenses:<ul>'
        for l in dataset.licenses.all():
            ret_string +=  ('<li property="dct:license" resource="%s">' % l.url_info)
            ret_string +=  ('<a href="{%s}">' % l.url_info)
            ret_string +=  ('<span property="dct:title">%s</span></a></li>' % l.name)
        if not dataset.licenses is None:
            ret_string += '</ul>'
        if dataset.version_released or dataset.dataset_structure.is_a_view:
            ret_string += '</p>'
        else:  
            ret_string += '<br>Click <a href="' + reverse('release_dataset', args=(DataSet_UKCL,)) + '" target="_blank">here</a> to release it.</p>'
        ret_string += '<hr>'
    return ret_string

@register.simple_tag
def browse_json_data(actual_instance, exported_json, esn, *args, **kwargs):
    json_data = json.loads(exported_json)[esn.model_metadata.name]
    
    return json_to_html(actual_instance, json_data, esn)

def json_to_html(actual_instance, json_data, esn, indent_level=0):
    try:
        ret_html = ""
        if esn.attribute == "":
            # no attribute, I am at the entry point
            ret_html = (indent_level * "--&nbsp;") + " " + esn.model_metadata.name + ': "<a href="' + json_data["UKCL"] + '">' + json_data[esn.model_metadata.name_field] +'</a>"<br>'
            ret_html += actual_instance.serialized_attributes(format = 'HTML')
        else:
            if esn.is_many:
                json_children = json_data[esn.attribute]
                esn.attribute = ""
                for json_child in json_children:
                    ext_json_child = {}
                    ext_json_child[esn.model_metadata.name] = json_child
                    ret_html += json_to_html(ext_json_child, esn, indent_level)
                return ret_html
            else:
                # there exist simple entities with no name
                try:
                    name = json_data[esn.model_metadata.name_field]
                except:
                    name = ""
                if name == "":
                    name = esn.attribute
                ret_html = (indent_level * "--&nbsp;") + " " + esn.model_metadata.name + ': "<a href="' + json_data["UKCL"] + '">' + name +'</a>"<br>'
        indent_level+=1
        for esn_child_node in esn.child_nodes.all():
            try:
                if esn_child_node.attribute == "":
                    ret_html += json_to_html(json_data, esn_child_node, indent_level)
                else:
                    ret_html += json_to_html(json_data[esn_child_node.attribute], esn_child_node, indent_level)
            except:
                pass
        return ret_html
    except Exception as e:
        return ""