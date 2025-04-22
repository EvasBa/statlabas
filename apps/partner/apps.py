import oscar.apps.partner.apps as apps


class PartnerConfig(apps.PartnerConfig):
    name = 'apps.partner'

    def ready(self):
        from . import models
        super().ready()
