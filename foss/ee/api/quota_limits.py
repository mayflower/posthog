from rest_framework import viewsets
from rest_framework.exceptions import NotFound


class QuotaLimitsViewSet(viewsets.ViewSet):
    """Quota limits are a PostHog Cloud billing feature; not available in the FOSS build."""

    lookup_field = "id"

    def list(self, request, *args, **kwargs):
        raise NotFound()

    def retrieve(self, request, *args, **kwargs):
        raise NotFound()
