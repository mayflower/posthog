from enum import StrEnum

from ee._foss import unavailable_class


class TaxonomyErrorMessages(StrEnum):
    UNAVAILABLE = "PostHog AI is not available in the FOSS build"


TaxonomyAgentToolkit = unavailable_class("TaxonomyAgentToolkit", "PostHog AI")
