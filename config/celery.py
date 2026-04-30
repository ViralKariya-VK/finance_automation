import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("finance_automation")

# This tells Celery to read config from Django's settings.py
# looking for any key that starts with CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Automatically find tasks.py in every installed app
app.autodiscover_tasks()