"""PostHog AI (Max) is an enterprise feature.

Products register their Max tools by subclassing ``MaxTool`` at import time, and several workflows import
agent internals at module level. These modules make those imports succeed; using the agent raises
``EnterpriseFeatureUnavailable``.
"""
