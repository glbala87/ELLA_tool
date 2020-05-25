import datetime
import jsonschema
import logging
import pytz

from api.config import config
from vardb.datamodel.jsonschemas import load_schema
from vardb.datamodel import sample, user, annotationshadow


log = logging.getLogger(__name__)


def deposit_filterconfigs(session, fc_configs):
    result = {"fc_updated": [], "fc_created": [], "ugfc_created": [], "ugfc_updated": []}
    filter_config_schema = load_schema("filterconfig_base.json")

    for fc_config in fc_configs:
        jsonschema.validate(fc_config, filter_config_schema)
        filterconfig = fc_config["filterconfig"]
        name = fc_config["name"]
        requirements = fc_config["requirements"]
        fc = {"name": name, "filterconfig": filterconfig, "requirements": requirements}

        existing = (
            session.query(sample.FilterConfig)
            .filter(
                sample.FilterConfig.name == fc["name"],
                sample.FilterConfig.date_superceeded.is_(None),
            )
            .one_or_none()
        )

        if (
            existing
            and fc["filterconfig"] == existing.filterconfig
            and fc["requirements"] == existing.requirements
        ):
            if not existing.active:
                log.warning(
                    "Filter config {} exists with same configuration, but is set as inactive. Will not be updated.".format(
                        existing
                    )
                )
            fc_obj = existing
        else:
            if existing:
                if not existing.active:
                    log.warning(
                        "Filter config {} already set as inactive. Will be set as superceeded.".format(
                            existing
                        )
                    )
                existing.date_superceeded = datetime.datetime.now(pytz.utc)
                fc["previous_filterconfig_id"] = existing.id
                existing.active = False

            # Check that filterconfig is supported by available annotationshadowfrequency columns
            annotationshadow.check_filterconfig(filterconfig, config)
            fc_obj = sample.FilterConfig(**fc)
            session.add(fc_obj)
            session.flush()
            if existing:
                result["fc_updated"].append(fc_obj.id)
            else:
                result["fc_created"].append(fc_obj.id)

        for usergroup in fc_config["usergroups"]:

            usergroup_name = usergroup["name"]
            usergroup_id = (
                session.query(user.UserGroup.id)
                .filter(user.UserGroup.name == usergroup_name)
                .scalar()
            )

            ugfc = {
                "usergroup_id": usergroup_id,
                "filterconfig_id": fc_obj.id,
                "order": usergroup["order"],
            }

            existing_ugfc = (
                session.query(sample.UserGroupFilterConfig)
                .filter(
                    sample.UserGroupFilterConfig.usergroup_id == usergroup_id,
                    sample.UserGroupFilterConfig.filterconfig_id == fc_obj.id,
                )
                .one_or_none()
            )

            if existing_ugfc and existing_ugfc.order != usergroup["order"]:
                log.info(
                    "Updating order of filterconfig {} for usergroup {} from {} to {}".format(
                        fc_obj, usergroup_name, existing_ugfc.order, usergroup["order"]
                    )
                )
                existing_ugfc.order = usergroup["order"]
                result["ugfc_updated"].append(existing_ugfc.id)
            elif not existing_ugfc:
                ugfc_obj = sample.UserGroupFilterConfig(**ugfc)
                session.add(ugfc_obj)
                session.flush()
                result["ugfc_created"].append(ugfc_obj.id)

    session.flush()

    return result
