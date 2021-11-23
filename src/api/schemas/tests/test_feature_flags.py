from __future__ import annotations

import json
import logging
import pytest
import random
import string
from typing import Dict, List, Optional

from api.config import config
from api.config.config import feature_is_enabled
from api.schemas.pydantic.v1 import validate_output, ResourceResponse, BaseModel, ExtraOK
from pydantic import ValidationError
from pydantic.json import pydantic_encoder

logger = logging.getLogger(__name__)


class PydanticModel(BaseModel):
    id: int
    desc: Optional[str] = None
    value: Optional[float] = 23.0


class PydanticExtra(PydanticModel, ExtraOK):
    id: int
    desc: Optional[str] = None
    value: Optional[float] = 42.0


class PydanticResource(ResourceResponse):
    __root__: List[PydanticModel]
    endpoint = "/api/v0/base/resource"


class PydanticExtraResource(PydanticExtra, ResourceResponse):
    endpoint = "/api/v0/extra/resource"


VALID_MODEL_DICTS: List[Dict] = [
    {"id": 1, "desc": "nice place you got here"},
    {"id": 2, "desc": None, "value": None},
    {"id": 3, "value": 5},
    {"id": 4},
    {"id": 5, "value": 10 / 6},
]

INVALID_MODEL_DICTS: List[Dict] = [
    {},
    {"id": "five"},
    {"id": 13, "desc": []},
    {"id": 14, "desc": "shame", "value": [1, 2]},
]

FEATURE_FLAGS: Dict[str, bool] = {k: v for k, v in config["app"].get("feature_flags", {}).items()}
PYDANTIC_FEATURE = "pydantic"
CNV_FEATURE = "cnv"


def toggle_feature(feature: str):
    new_val = not config["app"].get("feature_flags", {}).get(feature, False)
    _set_feature(feature, new_val)


def enable_feature(feature: str):
    _set_feature(feature, True)


def disable_feature(feature: str):
    _set_feature(feature, False)


def random_str(min_len: int = 4, max_len: int = 20) -> str:
    return "".join(
        [random.choice(string.ascii_letters) for _ in range(0, random.randint(min_len, max_len))]
    )


def _set_feature(feature: str, val: bool):
    if "feature_flags" not in config["app"]:
        config["app"]["feature_flags"] = {}
    config["app"]["feature_flags"][feature] = val


def serde(obj):
    # serialize/deserialize to ignore __root__, etc.
    if isinstance(obj, BaseModel):
        return json.loads(obj.json())
    else:
        return json.loads(json.dumps(obj, default=pydantic_encoder))


class TestFeatureFlags:
    def test_config_flags(self):
        for flag_name, val in FEATURE_FLAGS.items():
            logger.info(f"testing {flag_name}")
            assert feature_is_enabled(flag_name) is val
            toggle_feature(flag_name)
            assert feature_is_enabled(flag_name) is not val
            toggle_feature(flag_name)

    def test_pydantic_flag(self):
        for flag_status in [True, False]:
            logger.info(f"Testing with {PYDANTIC_FEATURE}={flag_status}")
            if flag_status:
                enable_feature(PYDANTIC_FEATURE)
            else:
                disable_feature(PYDANTIC_FEATURE)
            assert feature_is_enabled(PYDANTIC_FEATURE) is flag_status

            # should always be three
            list_obj = validate_basemodel(3, 0)
            assert len(serde(validate_basemodel(3, 0))) == 3
            if flag_status:
                assert isinstance(list_obj, PydanticResource)
            else:
                assert isinstance(list_obj, list)

            # should fail if flag_status is True
            if flag_status:
                with pytest.raises(ValidationError):
                    validate_basemodel(2, 1)
                    validate_basemodel(0, 2)
            else:
                assert len(validate_basemodel(2, 1)) == 3
                assert len(validate_basemodel(0, 2)) == 2

            # extraOK
            extra_obj = validate_extraok(should_pass=True)
            if flag_status:
                assert isinstance(extra_obj, PydanticExtraResource)
            else:
                assert isinstance(extra_obj, dict)
            extra_dict = serde(extra_obj)

            with pytest.raises(ValidationError):
                PydanticModel.parse_obj(extra_dict)

            if flag_status:
                with pytest.raises(ValidationError):
                    validate_extraok(False)
            else:
                extra_faildict = validate_extraok(False)
                # make sure the dict would in fact fail validation if enabled
                with pytest.raises(ValidationError):
                    PydanticExtra.parse_obj(extra_faildict)


@validate_output(PydanticResource)
def validate_basemodel(good_data: int, bad_data: int):
    resp = []
    while good_data > 0:
        resp.append(random.choice(VALID_MODEL_DICTS))
        good_data -= 1
    while bad_data > 0:
        resp.append(random.choice(INVALID_MODEL_DICTS))
        bad_data -= 1
    random.shuffle(resp)
    return resp


@validate_output(PydanticExtraResource)
def validate_extraok(should_pass: bool, num_extra: int = 2):
    if should_pass:
        base_dict = random.choice(VALID_MODEL_DICTS)
    else:
        base_dict = random.choice(INVALID_MODEL_DICTS)
    for _ in range(num_extra):
        base_dict[random_str()] = random_str()
    return base_dict
