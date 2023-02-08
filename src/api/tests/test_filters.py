import pytest
from sqlalchemy import func, tuple_
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import Grouping
from sqlalchemy.sql.selectable import ScalarSelect

from datalayer import filters
from vardb.datamodel import gene


def assert_results_equal(session, naive, refined, N):
    expected = session.query(gene.Gene).filter(naive).all()
    actual = session.query(gene.Gene).filter(refined).all()
    assert len(expected) == N
    assert expected == actual


def expressions_equal(naive, refined):
    # For some reason, direct equality comparison fails, but string comparison works
    # (and it outputs the whole SQL query)
    return str(naive.expression.compile(dialect=postgresql.dialect())) == str(
        refined.expression.compile(dialect=postgresql.dialect())
    )


@pytest.mark.parametrize(
    "attr",
    (
        gene.Gene.hgnc_id,  # int
        gene.Gene.hgnc_symbol,  # str
    ),
)
def test_filter_in_uses_naive_scalar(session, attr):
    # Test that filters.in_ uses naive implementation for small lists (<100)
    all_values = session.query(attr).order_by(func.random()).scalar_all()
    assert len(all_values) > 3000, "Expected more than 3000 genes in test database"

    # Should use naive implementation (right side is Grouping) with N < 100
    N = 99
    query_values = all_values[:N]
    naive = attr.in_(query_values)
    assert isinstance(naive.right, Grouping)
    refined = filters.in_(session, attr, query_values)
    assert isinstance(refined.right, Grouping)
    assert naive.left == refined.left == attr

    assert expressions_equal(naive, refined)
    assert_results_equal(session, naive, refined, N)

    # Should use refined implementation (right side is ScalarSelect)
    N = 101
    query_values = all_values[:N]
    naive = attr.in_(query_values)
    assert isinstance(naive.right, Grouping)
    refined = filters.in_(session, attr, query_values)
    assert isinstance(refined.right, ScalarSelect)
    assert naive.left == refined.left == attr

    assert not expressions_equal(naive, refined)
    assert_results_equal(session, naive, refined, N)


def test_filter_in_uses_naive_tuple(session):
    all_values = (
        session.query(gene.Gene.hgnc_id, gene.Gene.hgnc_symbol).order_by(func.random()).all()
    )

    # Should use naive implementation (right side is Grouping) with N < 100
    N = 99
    query_values = all_values[:N]
    naive = tuple_(gene.Gene.hgnc_id, gene.Gene.hgnc_symbol).in_(query_values)
    assert isinstance(naive.right, Grouping)
    refined = filters.in_(session, (gene.Gene.hgnc_id, gene.Gene.hgnc_symbol), query_values)
    assert isinstance(refined.right, Grouping)

    assert expressions_equal(naive, refined)
    assert_results_equal(session, naive, refined, N)

    # Should use refined implementation (right side is ScalarSelect)
    N = 101
    query_values = all_values[:N]
    naive = tuple_(gene.Gene.hgnc_id, gene.Gene.hgnc_symbol).in_(query_values)
    assert isinstance(naive.right, Grouping)
    refined = filters.in_(session, (gene.Gene.hgnc_id, gene.Gene.hgnc_symbol), query_values)
    assert isinstance(refined.right, ScalarSelect)

    assert not expressions_equal(naive, refined)
    assert_results_equal(session, naive, refined, N)


@pytest.mark.parametrize(
    "use_subquery",
    (True, False),
)
def test_filter_with_query(session, use_subquery):
    all_values = session.query(gene.Gene.hgnc_id).order_by(gene.Gene.hgnc_symbol).limit(100)
    if use_subquery:
        all_values = all_values.subquery()

    naive = gene.Gene.hgnc_id.in_(all_values)
    refined = filters.in_(session, gene.Gene.hgnc_id, all_values)

    assert expressions_equal(naive, refined)
    assert_results_equal(session, naive, refined, 100)
