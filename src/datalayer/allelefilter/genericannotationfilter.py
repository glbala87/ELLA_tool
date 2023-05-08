import operator
from typing import Any, Dict, List, Set, Tuple, Union

from sqlalchemy import Numeric, and_, cast, func, literal_column, or_
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.selectable import Alias
from sqlalchemy.types import Integer
from api.util.util import query_print_table

from datalayer import filters
from vardb.datamodel import annotation

OPERATORS = {
    "==": operator.eq,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
}


class GenericAnnotationFilter(object):
    def __init__(self, session: Session, config: Dict[str, Any]) -> None:
        self.session = session
        self.config = config

    def _build_subquery(self, filter_config: Dict[str, Any]):
        subquery_columns = []

        path = "annotations->" + "->".join([f"'{x}'" for x in filter_config["target"].split(".")])

        if filter_config["is_array"]:
            target = f"jsonb_array_elements({path})"
        else:
            target = f"{path}"

        for cfg in filter_config["config"]:
            key = cfg["key"]
            label = filter_config["target"] + "." + key
            subquery_columns.append(
                cast(literal_column(f"{target}->'{key}'"), Numeric).label(label)
            )

        return self.session.query(annotation.Annotation.allele_id, *subquery_columns).subquery()

    def _build_filters(self, filter_config: Dict[str, Any], subquery):
        # Build filters
        subquery_filters = []

        for cfg in filter_config["config"]:
            key = cfg["key"]

            label = filter_config["target"] + "." + key
            op = OPERATORS[cfg["operator"]]
            value = cfg["value"]
            subquery_filters.append(op(getattr(subquery.c, label), value))
        return subquery_filters

    def filter_alleles(
        self, gp_allele_ids: Dict[Tuple[str, str], List[int]], filter_config: Dict[str, Any]
    ) -> Dict[Tuple[str, str], Set[int]]:
        """
        Filter alleles on generic annotation.

        filter_config is specified like
        {
            "target": "prediction.spliceai",
            "is_array": True,
            "config": [
                {"key": "DS_AG", "operator": "<", "value": 0.05},
                {"key": "DS_AL", "operator": "<", "value": 0.05},
                {"key": "DS_DG", "operator": "<", "value": 0.05},
                {"key": "DS_DL", "operator": "<", "value": 0.05},
            ],
            "mode": "all",
        }
        """
        if filter_config.get("mode", "all") == "all":
            bool_operator = and_
        elif filter_config["mode"] == "any":
            bool_operator = or_
        else:
            raise RuntimeError(f"Unknown filter mode: {filter_config['mode']}")

        subquery = self._build_subquery(filter_config)
        subquery_filters = self._build_filters(filter_config, subquery)

        result: Dict[Tuple[str, str], Set[int]] = dict()
        for gp_key, allele_ids in gp_allele_ids.items():
            filtered_allele_ids = self.session.query(subquery.c.allele_id, *subquery.c).filter(
                filters.in_(self.session, subquery.c.allele_id, allele_ids),
                bool_operator(
                    *subquery_filters,
                ),
            )

            query_print_table(filtered_allele_ids)

            result[gp_key] = set([x[0] for x in filtered_allele_ids.all()])

        return result


if __name__ == "__main__":
    from vardb.util.db import DB

    db = DB()
    db.connect()
    session = db.session

    config = {
        "target": "prediction.spliceai",
        "is_array": True,
        "config": [
            {"key": "DS_AG", "operator": "<", "value": 0.05},
            {"key": "DS_AL", "operator": "<", "value": 0.05},
            {"key": "DS_DG", "operator": "<", "value": 0.05},
            {"key": "DS_DL", "operator": "<", "value": 0.05},
        ],
        "mode": "all",
    }

    s = GenericAnnotationFilter(session, config)
    s.filter_alleles({("foo", "bar"): list(range(700, 800))}, config)
