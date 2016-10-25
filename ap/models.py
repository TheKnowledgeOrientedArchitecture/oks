# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from django.contrib.auth.models import User
from django.db import models
from knowledge_server.models import ShareableModel, ModelMetadata, DataSetStructure, DataSet, Workflow, WorkflowStatus


class Widget(ShareableModel):
    '''
    It is a django widget; TBC
    '''
    widgetname = models.CharField(max_length=255, blank=True)


class AttributeType(ShareableModel):
    name = models.CharField(max_length=255, blank=True)
    widgets = models.ManyToManyField(Widget, blank=True)  # TODO farlo passare da una classe e aggiungere attributo default


class Attribute(ShareableModel):
    name = models.CharField(max_length=255, blank=True)
    model_metadata = models.ForeignKey(ModelMetadata, null=True, blank=True)
    type = models.ForeignKey(AttributeType)

    def __str__ ( self ):
        return self.simple_entity.name + "." + self.name


# ASSERT: I metodi di un wf devono avere impatto solo su ModelMetadata contenute nella struttura
#     tutte le istanze nei nodi del DSS condividono lo stato del DataSet


class WorkflowMethod(ShareableModel):
    '''
    '    It describes an operation of a workflow
    '
    '    If there are no initial_statuses then this is a method which creates the entity
    '    TODO: The final status be dynamically determined by the implementation, HOW ?
    '    WorkflowMethod E Method ERANO CLASSI SEPARATE, PERCHÉ?
    '''
    initial_statuses = models.ManyToManyField(WorkflowStatus, blank=True, related_name="+")
    final_status = models.ForeignKey(WorkflowStatus, blank=True, related_name="+")
    workflows = models.ManyToManyField(Workflow, related_name="methods")
    attributes = models.ManyToManyField(Attribute, through='AttributeInAMethod')
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    create_instance = models.BooleanField(default=False)
    # script_precondition is a ?JSON? script that evaluates to True if the method can be executed on the dataset;
    # it can be used to perform controls other than on permissions
    script_precondition = models.TextField(blank=True)
    # script_postcondition ??? what's for?
    script_postcondition = models.TextField(blank=True)
    # script_premethod name of a method to be invoked before
    script_premethod = models.TextField(blank=True)
    script_postmethod = models.TextField(blank=True)


class AttributeInAMethod(ShareableModel):
    '''
    '''
    attribute = models.ForeignKey(Attribute)
    # workflow is blank unless the attribute is a DataSet or a set of entities; it can be blank if a method is specified
    # TODO: chiarire il commento di sopra: significa che entità collegate possono avere un sotto workflow?
    # workflow = models.ForeignKey(Workflow, blank=True, null=True)
    # method (inline) ???????
    implementation_method = models.ForeignKey(WorkflowMethod, blank=True, null=True)
    # TODO: forse andra' aggiunta qualche informazione per indicare come implementare (e.g. inline)
    custom_widget = models.ForeignKey(Widget, blank=True, null=True)


class WorkflowTransition():
    '''
    '    It describes the execution of a method 
    '''
    instance = models.ForeignKey(DataSet, related_name='transitions')
    workflow_method = models.ForeignKey(WorkflowMethod)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    notes = models.TextField()
    #     user = models.ForeignKey('userauthorization.KUser')
    # a method can have several possible initial and final states; actaul ones are stored here
    actual_status_from = models.ManyToManyField(WorkflowStatus, blank=True, related_name="+")
    actual_status_to = models.ManyToManyField(WorkflowStatus, related_name="+")


class Application(ShareableModel):
    '''
    '    An application can do what its workflows describe
    '    Within an application a user can
    '        - Run a method that creates also the dataset (see class WorkflowMethod)
    '        - Search on datasets of the types/structures managed by the application
    '            - on those without a workflow a compatible workflow can be applied
    '            - on those within a workflow (of the application) a list of methods can be applied (filtered by status, permission, ...)
    '''
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=2000, blank=True)
    workflows = models.ManyToManyField(Workflow, related_name="applications")

    def __str__ ( self ):
        return self.name


class PermissionHolder(ShareableModel):
    pass


class PermissionStatement(ShareableModel):
    '''
    '    It states that a PermissionHolder can perform something
    '''
    permission_holder = models.ForeignKey(PermissionHolder)
    methods = models.ManyToManyField(WorkflowMethod, blank=True, related_name='permission')


class KSUser(ShareableModel):
    user = models.ForeignKey(User, blank=True, null=True)  # id_user = models.IntegerField(default=1)
    name = models.CharField(max_length=255, blank=True)
    surname = models.CharField(max_length=255, blank=True)
    permission_holder = models.OneToOneField(PermissionHolder)

    def __str__ ( self ):
        return self.name + " " + self.surname + (" (" + self.user.username + ")" if self.user else "")


class KSRole(ShareableModel):
    name = models.CharField(max_length=255, blank=True)
    permission_holder = models.OneToOneField(PermissionHolder)
    users = models.ManyToManyField(KSUser, related_name="roles")

    def __str__ ( self ):
        return self.name


class KSGroup(ShareableModel):
    name = models.CharField(max_length=255, blank=True)
    permission_holder = models.OneToOneField(PermissionHolder)
    users = models.ManyToManyField(KSUser, related_name="groups")

    def __str__ ( self ):
        return self.name
