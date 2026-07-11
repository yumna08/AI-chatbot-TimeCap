from django.apps import AppConfig


class CapsulesConfig(AppConfig):
    name = 'capsules'

    def ready(self):
        import capsules.signals
