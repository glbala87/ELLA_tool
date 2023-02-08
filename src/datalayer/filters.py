from typing import Iterable, Tuple, Union, overload

from sqlalchemy import cast, func, tuple_
from sqlalchemy.dialects.postgresql import ARRAY, array
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.expression import false

# from sqlalchemy.orm.attributes import ColumnOperators
from sqlalchemy.sql.operators import ColumnOperators
from sqlalchemy.sql.selectable import Selectable
from sqlalchemy.types import Integer, String


@overload
def in_(
    session: Session,
    attr: Tuple[ColumnOperators, ...],
    values: Iterable[Tuple[Union[str, int], ...]],
):
    ...


@overload
def in_(
    session: Session,
    attr: ColumnOperators,
    values: Iterable[Union[str, int]],
):
    ...


@overload
def in_(
    session: Session,
    attr: Union[ColumnOperators, Iterable[ColumnOperators]],
    values: Union[Query, Selectable],
):
    ...


def in_(
    session: Session,
    attr: Union[ColumnOperators, Iterable[ColumnOperators]],
    values: Union[Iterable[Union[str, int, Tuple[Union[str, int], ...]]], Union[Query, Selectable]],
):
    """
    A drop-in replacement for sqlalchemy's `in_` filter, that uses a subquery with unnest
    for performance (if length of values is above 100).

    See https://levelup.gitconnected.com/why-is-in-query-slow-on-indexed-column-in-postgresql-b716d9b563e2
    for an explanation of why this is the case.

    The following are functionally equivalent:

    ```
    session.query(
        Allele
    ).filter(
        in_(
            session,
            Allele.id,
            (1,2,3),
        )
    )
    ```

    and

    ```
    session.query(
        Genepanel
    ).filter(
        Allele.id.in_([1,2,3])
    )
    ```

    The first example is generally more efficient, as it uses a subquery with unnest, which avoids
    a sequential scan of the genepanel table for large numbers of values.

    Similarly, the following are functionally equivalent:

    ```
    session.query(
        Genepanel
    ).filter(
        in_(
            session,
            (Genepanel.name, Genepanel.version),
            (("panel1", "v01"), ("panel2", "v02")),
        )
    )
    ```

    and

    ```
    session.query(
        Genepanel
    ).filter(
        tuple_(
            Genepanel.name,
            Genepanel.version
        ).in_(
            [("panel1", "v01"), ("panel2", "v02")]
        )
    )
    ```

    """
    if isinstance(attr, Iterable):
        attr = tuple_(*attr)
    if isinstance(values, (Query, Selectable)):
        return attr.in_(values)

    if not isinstance(values, (list, tuple)):
        values = list(values)

    if not values:
        # Empty list, return a filter that will never match
        return false()

    if len(values) < 100:
        # Use the default in_ filter for small lists
        return attr.in_(values)

    if isinstance(values[0], tuple):
        assert isinstance(values[0][0], str) or isinstance(values[0][0], int)
        # map(list, zip(*values)))
        # is equivalent to
        # [[k[0] for k in values], [k[1] for k in values]],
        # for a list of tuples of length 2, but more generic
        # (assuming all tuples have the same length)
        q = session.query("*").select_from(func.unnest(*map(list, zip(*values))))
        return attr.in_(q)

    assert isinstance(attr, ColumnOperators)

    if isinstance(values[0], str):
        cast_type = String
    elif isinstance(values[0], int):
        cast_type = Integer
    else:
        raise ValueError(f"Unsupported type: {type(values[0])}")

    return attr.in_(session.query(func.unnest(cast(array(values), ARRAY(cast_type)))))
