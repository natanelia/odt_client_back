from django.db import models
from django_roa import Model as ROAModel
from ta.reference import ReferenceField
from rest_framework import serializers, routers, viewsets

class CommonROAModel(ROAModel):
    class Meta:
        abstract = True

    @classmethod
    def get_resource_url_list(cls):
        return u'http://127.0.0.1:8000/ta/%s/' % (cls.api_base_name)

    def get_resource_url_count(self):
        return self.get_resource_url_list()

