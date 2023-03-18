import django.dispatch

config_updated = django.dispatch.Signal(['key', 'old_value', 'new_value'])
