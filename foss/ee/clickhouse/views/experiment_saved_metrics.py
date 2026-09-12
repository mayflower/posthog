"""Experiments are an enterprise API; core serializers nest this one at class-definition time."""

from rest_framework import serializers


class ExperimentToSavedMetricSerializer(serializers.Serializer):
    pass
