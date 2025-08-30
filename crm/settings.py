INSTALLED_APPS = [
    "django_crontab",
    "django_celery_beat",
]

CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
]
