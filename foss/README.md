# FOSS build

This directory makes the Docker image built from this fork a pure MIT build of PostHog.
Upstream's `ee/` tree carries a proprietary license and must not ship in that image.

## What is in here

- `ee/` is an MIT replacement for the enterprise package, written from scratch.
  The `Dockerfile` copies it into the image in place of upstream's `ee/`.
  It owns the `ee` Django app label for the MIT access-control models that carry it
  (`products/access_control/backend/models`), ships a migration chain with the same node names core depends on,
  and provides the modules that core imports unconditionally.
- `check_ee_shim.py` parses core for every `ee` import and imports each one against the shim.
  It fails when core starts importing something the shim does not provide.
- `smoke.py` boots the image like each process type (web, Temporal, Celery) and migrates a fresh database.

`.github/workflows/mayflower-container-images.yml` runs both scripts inside the freshly built image before it pushes.

## Why a shim instead of removing the imports

Upstream no longer builds or tests the tree without `ee/`.
Core imports `ee` at module level from about a hundred files, core models have foreign keys to `ee.Role`, and core migrations depend on `ee` migration nodes.
Patching all of that in the fork would conflict on every rebase.
The shim keeps the core diff to two lines in `posthog/settings/`, and drift shows up as a failed `check_ee_shim.py` run instead of a broken image.

## How the shim behaves

- `ee.apps.EnterpriseConfig`, `ee.urls`, `ee.settings` and `ee.models.license` are deliberately absent.
  Core checks for them with `EE_AVAILABLE` gates and `try/except ImportError`, and takes its FOSS branch when they are missing.
- `ee.apps.FossConfig` is installed by `posthog/settings/web.py` so the `ee` label exists.
- `ee.foss_settings` defines, from environment variables, the settings core reads but upstream only declares in the enterprise tree (LLM provider keys, Customer.io, Google OAuth, the materialized-column cron).
- Quota limiting never limits. Billing raises `EnterpriseFeatureUnavailable`. Materialized columns report none, so HogQL reads properties from JSON.
- Generic helpers core relies on at request time (`async_to_sync`, `SyncIterableToAsync`, the untrusted-data markers, SCIM masking) are implemented for real.
- Everything else (PostHog AI, Salesforce enrichment, subscription delivery, Vercel) exists only so imports succeed, and raises `EnterpriseFeatureUnavailable` when called.

## What the FOSS build does not have

Everything upstream registers from `ee/urls.py`: roles and RBAC endpoints, experiments, groups, subscriptions, billing, quota limits, SCIM, PostHog AI, and the enterprise person and event-definition views.
This matches upstream's own FOSS boundary.

## After a rebase

```bash
rm -rf /tmp/foss-tree && git worktree add --detach /tmp/foss-tree HEAD
rm -rf /tmp/foss-tree/ee && cp -r foss/ee /tmp/foss-tree/ee
cd /tmp/foss-tree && DEBUG=1 OPT_OUT_CAPTURE=1 python foss/check_ee_shim.py
```

A failure lists the new symbols core imports.
Add them to the shim with the same discipline: implement generic helpers, make quota and billing safe no-ops, and let enterprise features raise.
If core adds a migration that depends on a new `ee` node, add a no-op migration with that name to `ee/migrations/`.

## Using the image with mayflower/posthog-helm

The chart's `images.app` entry takes the FOSS image directly. Every workload and job that runs the app image (web, Celery worker, the Temporal workers, migrate, async migrations check) uses the same entrypoints as upstream, and the image keeps upstream's uid 10001.

```yaml
images:
  app:
    repository: ghcr.io/mayflower/posthog-foss
    tag: <commit sha> # every verified build pushes its commit tag; master also moves the master tag
  node:
    repository: ghcr.io/mayflower/posthog-node
    tag: master
```

The Temporal workers for Max AI and LLM evals are disabled in the chart by default; leave them off, the FOSS build has no agent to run.
