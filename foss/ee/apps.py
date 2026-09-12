from django.apps import AppConfig


class FossConfig(AppConfig):
    """Owns the ``ee`` app label for the MIT access-control models that declare it.

    There is intentionally no ``EnterpriseConfig`` here: core checks for that name to decide whether
    enterprise features are available.
    """

    name = "ee"
    label = "ee"
    verbose_name = "Access control (FOSS)"
