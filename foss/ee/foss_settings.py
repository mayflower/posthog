"""FOSS defaults for settings that core code reads but that upstream only defines in the enterprise tree.

Every value comes from the environment so a self-hosted operator can still wire up an LLM provider or
Customer.io without patching code. Nothing here enables an enterprise feature.
"""

import os

from posthog.settings.utils import get_from_env

# LLM providers used by product features that call a model directly.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
REPLAY_VISION_GEMINI_API_KEY = os.getenv("REPLAY_VISION_GEMINI_API_KEY", GEMINI_API_KEY)
INKEEP_API_KEY = os.getenv("INKEEP_API_KEY", "")
AZURE_INFERENCE_ENDPOINT = os.getenv("AZURE_INFERENCE_ENDPOINT", "")
AZURE_INFERENCE_CREDENTIAL = os.getenv("AZURE_INFERENCE_CREDENTIAL", "")
LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "")
LLM_GATEWAY_API_KEY = os.getenv("LLM_GATEWAY_API_KEY", "")

# Transactional email through Customer.io (optional; SMTP still works without it).
CUSTOMER_IO_API_KEY = os.getenv("CUSTOMER_IO_API_KEY", "")
CUSTOMER_IO_API_URL = os.getenv("CUSTOMER_IO_API_URL", "https://api.customer.io")

# Google login and Google integrations.
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", "")

# Billing service is a PostHog Cloud component; the admin only shows a link when this is set.
BILLING_SERVICE_URL = os.getenv("BILLING_SERVICE_URL", "")

# Local development helper.
DEV_API_KEY = os.getenv("DEV_API_KEY", "")

# Materialized columns are managed by the enterprise ClickHouse tooling; the FOSS shim makes the
# scheduled task a no-op, but the beat schedule still needs a valid cron expression.
MATERIALIZE_COLUMNS_SCHEDULE_CRON = get_from_env("MATERIALIZE_COLUMNS_SCHEDULE_CRON", "0 5 * * *")
