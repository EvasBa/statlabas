from oscar.apps.catalogue.apps import CatalogueConfig as BaseCatalogueConfig

class CatalogueConfig(BaseCatalogueConfig):
    name = 'apps.catalogue'

    def ready(self):
        from . import models
        super().ready()