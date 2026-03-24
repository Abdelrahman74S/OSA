from django.apps import AppConfig
import accounts


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        import accounts.signals