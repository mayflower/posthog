# ruff: noqa: T201, PLC0415 -- a CLI script that prints its report and boots Django on demand
"""Boot the FOSS image the way each process type does and fail on the first import error.

Runs inside the built image (``python foss/smoke.py``) with ``DATABASE_URL`` and ``REDIS_URL`` set:

1. ``django.setup()`` plus the URL conf, WSGI and ASGI entry points (web).
2. The Temporal worker command module, which imports every workflow (temporal workers).
3. Celery task autodiscovery (celery workers and beat).
4. ``manage.py migrate`` against the provided database, then ``manage.py check``.
"""

import os
import sys
import importlib
import subprocess

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "posthog.settings")


def step(label: str) -> None:
    print(f"--- {label}", flush=True)


def main() -> int:
    import django

    step("django.setup()")
    django.setup()

    for module in (
        "posthog.api.rest_router",
        "posthog.urls",
        "posthog.wsgi",
        "posthog.asgi",
        "posthog.management.commands.start_temporal_worker",
    ):
        step(f"import {module}")
        importlib.import_module(module)

    step("celery autodiscovery")
    from posthog.celery import app

    app.loader.import_default_modules()
    app.autodiscover_tasks(force=True)
    print(f"{len(app.tasks)} celery tasks registered")

    from django.conf import settings

    if "ee.apps.EnterpriseConfig" in settings.INSTALLED_APPS or settings.EE_AVAILABLE:
        print("FAIL: enterprise app is installed; this is not a FOSS build")
        return 1

    for command in (["migrate", "--noinput"], ["check"]):
        step(f"manage.py {' '.join(command)}")
        subprocess.run([sys.executable, "manage.py", *command], check=True)

    print("OK: FOSS image boots for web, temporal and celery, and migrates a fresh database")
    return 0


if __name__ == "__main__":
    sys.exit(main())
