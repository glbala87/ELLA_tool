from __future__ import annotations

from typing import Dict, Optional

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.users import User


class GeneAssessment(BaseModel):
    id: int
    date_created: str
    date_superceeded: Optional[str] = None
    gene_id: int
    genepanel_name: str
    genepanel_version: str
    analysis_id: Optional[int] = None
    previous_assessment_id: Optional[int] = None
    user_id: int
    usergroup_id: int
    user: User
    seconds_since_update: int
    evaluation: Optional[Dict] = None
