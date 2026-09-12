"""Enterprise models that core references at import time, as unmanaged placeholders.

``License``, ``DashboardPrivilege``, ``EnterpriseEventDefinition`` and ``EnterprisePropertyDefinition`` are
deliberately absent: core imports them inside ``try/except ImportError`` or behind ``EE_AVAILABLE``.
"""

from .explicit_team_membership import ExplicitTeamMembership
from .scim_provisioned_user import SCIMProvisionedUser
from .scim_request_log import SCIMRequestLog

__all__ = ["ExplicitTeamMembership", "SCIMProvisionedUser", "SCIMRequestLog"]
