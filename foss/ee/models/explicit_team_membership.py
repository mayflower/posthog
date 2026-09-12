from django.db import models

from posthog.models.utils import UUIDTModel


class ExplicitTeamMembership(UUIDTModel):
    """Project-level membership is an enterprise feature; this placeholder only satisfies signal wiring."""

    class Meta:
        app_label = "ee"
        managed = False
        db_table = "ee_explicitteammembership"

    team = models.ForeignKey("posthog.Team", on_delete=models.CASCADE, related_name="+")
    parent_membership = models.ForeignKey("posthog.OrganizationMembership", on_delete=models.CASCADE, related_name="+")
    level = models.PositiveSmallIntegerField(default=1)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
