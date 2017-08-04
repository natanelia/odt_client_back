import os
import urllib2
import json
import copy
import pprint
from django.core.management.base import BaseCommand, CommandError
from ta_client.settings import *

pp = pprint.PrettyPrinter(indent=2)

class Command(BaseCommand):

    def handle(self, *args, **options):

        res = urllib2.urlopen(TA_CLIENT_SYNC_URL).read()

        models = json.loads(res)
        for m in models:
            model_path = m['class_path'].replace('.', '/')
            k = model_path.rfind('/')
            dir_path = '%s/%s' % (TA_CLIENT_SYNC_PATH, model_path[:k])

            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            # create model file
            model_file = open('%s/%s.py' % (dir_path, model_path[k:]), 'w+')
            
            # write default model import
            model_file.write(
"""
import jsonfield
import django
import ta
import ta_models
from django.db import models
from rest_framework import serializers
from ta_client.models import CommonROAModel

"""
            )

            model_file.close()

        # create init files to make class importable
        init_file = open('%s/__init__.py' % TA_CLIENT_SYNC_PATH, 'w+')
        init_file.close()

        for subdir, dirs, files in os.walk(TA_CLIENT_SYNC_PATH):
            for dir in dirs:
                init_file = open('%s/__init__.py' % os.path.join(subdir, dir), 'w+')
                init_file.close()



        model_text_data = {}
        for m in models:
            model_path = m['class_path'].replace('.', '/')
            file_path = '%s/%s' % (TA_CLIENT_SYNC_PATH, model_path)
            
            if file_path not in model_text_data.keys():
                model_text_data[file_path] = {}
            

            # write model classes
            class_text = 'class TA_%s(CommonROAModel):\n' % m['class_name']
            class_text += '\tapi_base_name = "%s/%s"\n\n' % (model_path, m['class_name'].lower())

            dependencies = []
            fields_comma_seperated = []
            for f in m['fields']:
                if not f.get('relation', None):
                    if f['class_path'] == 'ta.reference' and f['class_name'] == 'ReferenceField':
                        class_text += (
'\t%s = %s.%s("%s", "%s", help_text="%s")\n' % (
                            f['name'],
                            f['class_path'],
                            f['class_name'],
                            f['key_label'],
                            f['value_label'],
                            f['help_text'])
                        )
                        fields_comma_seperated.append(f['name'])
                    elif f['class_name'] != 'AutoField':
                        class_text += (
'\t%s = %s.%s(max_length=%s, null=%s, blank=%s, help_text="%s"%s)\n' % (
                            f['name'],
                            f['class_path'],
                            f['class_name'],
                            '"%s"' % f['max_length'] if f.get('max_length', None) is not None else 'None',
                            f['null'],
                            True,
                            f['help_text'],
                            ', decimal_places=%d, max_digits=%d' % (f.get('decimal_places'), f.get('max_digits')) if f['class_name'] == 'DecimalField' else ''
)
                        )
                        fields_comma_seperated.append(f['name'])
                else:
                    related_model_full_name = '%s.%s' % (f['related_model_path'], f['related_model_name'])
                    if m['class_path'] != f['related_model_path']:
                        corr_rel = '%s.%s.TA_%s' % (
                            TA_CLIENT_SYNC_MODULE,
                            f['related_model_path'],
                            f['related_model_name'])
                    else:
                        corr_rel = '"TA_%s"' % f['related_model_name']

                    class_text += (
'\t%s = %s.%s(%s, related_name=%s, null=%s, blank=%s, help_text="%s")\n' % (
                        f['name'],
                        f['class_path'],
                        f['class_name'],
                        corr_rel,
                        '"%s"' % f['related_name'] if f.get('related_name', None) is not None else 'None',
                        f['null'],
                        True,
                        f['help_text'].replace('"', "'"))
                    )
                    fields_comma_seperated.append(f['name'])

                    if related_model_full_name not in dependencies and m['class_path'] != f['related_model_path']:
                        dependencies.append(related_model_full_name)
                    elif f['related_model_name'] not in dependencies and m['class_path'] == f['related_model_path']:
                        if m['class_name'] != f['related_model_name']:
                            dependencies.append(f['related_model_name'])

            class_text += (
"""
\t@classmethod
\tdef serializer(cls):
\t\treturn %sSerializer
""" % (m['class_name'])
            )

            class_text += (
"""
class %sSerializer(serializers.ModelSerializer):
\tclass Meta:
\t\tmodel = TA_%s
\t\tfields = %s
""" % (m['class_name'], m['class_name'], tuple(fields_comma_seperated))
            )

            class_text += ('\n\n')

            model_text_data[file_path][m['class_name']] = {
                'dependencies': dependencies,
                'text': class_text,
            }

        
        for file_path, model_data in model_text_data.iteritems():
            external_classes = []
            ordered_class_texts = []

            before_size = -1
            inserted_model_data = {}
            while len(model_data) > 0 and before_size != len(model_data):
                before_size = len(model_data)
                for c in inserted_model_data:
                    for k, k_data in model_data.items():
                        if c in k_data['dependencies']:
                            k_data['dependencies'].remove(c)
                
                for c, c_data in model_data.items():
                    if len(c_data['dependencies']) == 0:
                        ordered_class_texts.append(c_data['text'])
                        inserted_model_data[c] = model_data.pop(c, None)
            
            if len(model_data):
                for c, c_data in model_data.items():
                    for d in c_data['dependencies']:
                        if d not in external_classes:
                            external_classes.append(d)


                for c, c_data in model_data.items():
                    ordered_class_texts.append(c_data['text'])
                    inserted_model_data[c] = model_data.pop(c, None)

                # print '>>> %s' % file_path
                # for c, c_data in model_data.items():
                #     print '    FAILED TO OUTPUT %s WITH DEPS = %s' % (c, c_data['dependencies'])



            # create model file
            model_file = open('%s.py' % file_path, 'a')

            for ec in external_classes:
                k = ec.rfind('.')
                if k > -1:
                    model_file.write('from %s.%s import TA_%s\n' % (TA_CLIENT_SYNC_MODULE, ec[:k], ec[k+1:]))
            
            for oct in ordered_class_texts:
                model_file.write('%s\n' % oct)
            model_file.close()