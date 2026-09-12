"""The Vercel marketplace integration is a PostHog Cloud feature.

The router imports these submodules at module level but only registers their viewsets when
``EE_AVAILABLE`` is true, so empty modules are enough.
"""
