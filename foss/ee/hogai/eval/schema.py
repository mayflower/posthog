"""Evaluation snapshot schemas, used only by the AI evaluation Dagster jobs."""

from pydantic import BaseModel


class BaseSnapshot(BaseModel):
    model_config = {"extra": "allow"}


class ActorsPropertyTaxonomySnapshot(BaseSnapshot):
    pass


class ClickhouseTeamDataSnapshot(BaseSnapshot):
    pass


class DataWarehouseTableSnapshot(BaseSnapshot):
    pass


class GroupTypeMappingSnapshot(BaseSnapshot):
    pass


class PostgresTeamDataSnapshot(BaseSnapshot):
    pass


class PropertyDefinitionSnapshot(BaseSnapshot):
    pass


class PropertyTaxonomySnapshot(BaseSnapshot):
    pass


class TeamTaxonomyItemSnapshot(BaseSnapshot):
    pass


class TeamSnapshot(BaseSnapshot):
    pass


class TeamEvaluationSnapshot(BaseSnapshot):
    pass


class DatasetInput(BaseSnapshot):
    pass


class EvalsDockerImageConfig(BaseSnapshot):
    pass


__all__ = [name for name in dir() if name[0].isupper() and name != "Any" and name != "BaseModel"]
