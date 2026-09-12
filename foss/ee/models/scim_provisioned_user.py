from django.db import models

from posthog.models.utils import UUIDTModel


class SCIMProvisionedUser(UUIDTModel):
    """SCIM provisioning is an enterprise feature; this placeholder keeps the admin inline valid."""

    class Meta:
        app_label = "ee"
        managed = False
        db_table = "ee_scimprovisioneduser"

    user = models.ForeignKey("posthog.User", on_delete=models.CASCADE, related_name="+")
    organization_domain = models.ForeignKey(
        "posthog.OrganizationDomain", on_delete=models.CASCADE, related_name="+", null=True
    )
    identity_provider_config = models.ForeignKey(
        "posthog.IdentityProviderConfig", on_delete=models.CASCADE, related_name="+", null=True
    )
    identity_provider = models.CharField(max_length=64, blank=True)
    username = models.CharField(max_length=254, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
