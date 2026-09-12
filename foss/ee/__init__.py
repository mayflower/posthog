"""FOSS replacement for the enterprise ``ee`` package.

The upstream ``ee/`` tree carries a proprietary license. This package is written from
scratch under the MIT license and only does three things:

1. Owns the ``ee`` Django app label so the MIT access-control models that carry it
   (``products/access_control/backend/models``) keep their tables and migration history.
2. Provides the modules that core code imports unconditionally, with FOSS-safe behavior: quota limiting
   never limits, billing is unavailable, and enterprise-only helpers raise ``EnterpriseFeatureUnavailable``.
3. Deliberately omits ``ee.apps.EnterpriseConfig``, ``ee.urls``, ``ee.settings`` and ``ee.models.license`` so
   that the ``EE_AVAILABLE`` gates and ``try: ... except ImportError`` fallbacks in core select the FOSS paths.

``foss/check_ee_shim.py`` verifies that every module core imports unconditionally exists here.
"""
