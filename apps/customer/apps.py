import oscar.apps.customer.apps as apps


class CustomerConfig(apps.CustomerConfig):
    name = 'apps.customer'

    def ready(self):
        from . import models
        super().ready()

    
