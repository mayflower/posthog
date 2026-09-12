from django.db import models

from posthog.models.utils import UUIDTModel


class SCIMRequestLog(UUIDTModel):
    """SCIM request logging is an enterprise feature; this placeholder keeps the core serializer valid."""

    class Meta:
        app_label = "ee"
        managed = False
        db_table = "ee_scimrequestlog"

    organization_domain = models.ForeignKey(
        "posthog.OrganizationDomain", on_delete=models.CASCADE, related_name="+", null=True
    )
    identity_provider_config = models.ForeignKey(
        "posthog.IdentityProviderConfig", on_delete=models.CASCADE, related_name="+", null=True
    )
    request_method = models.CharField(max_length=16)
    request_path = models.TextField()
    request_headers = models.JSONField(null=True)
    request_body = models.TextField(null=True)
    response_status = models.IntegerField()
    response_body = models.TextField(null=True)
    identity_provider = models.CharField(max_length=64, blank=True)
    duration_ms = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
