from django.conf import settings
import os.path

def get(key, default):
  return getattr(settings, key, default)

TA_CLIENT_SYNC_URL = get('TA_CLIENT_SYNC_URL', 'http://127.0.0.1:8000/ta/__model-sync__')
TA_CLIENT_SYNC_MODULE = get('TA_CLIENT_SYNC_MODULE', 'ta_models')
TA_CLIENT_SYNC_PATH = get('TA_CLIENT_SYNC_PATH', os.path.dirname(os.path.realpath(settings.ROOT_URLCONF)) + '/' + TA_CLIENT_SYNC_MODULE)