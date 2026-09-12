"""Salesforce enrichment syncs PostHog Cloud usage into Salesforce.

The Temporal workflows that use it are scheduled by default, so the read helpers report an empty
dataset and the workflows complete as no-ops instead of failing on every run.
"""
