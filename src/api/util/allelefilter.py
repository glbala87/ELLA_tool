import datetime
from collections import defaultdict
from sqlalchemy import or_, and_, tuple_, column, Float, String, table, Integer
from sqlalchemy.dialects.postgresql import JSONB
from vardb.datamodel import sample, workflow, assessment, allele, gene, annotation

from api.util.util import query_print_table
from api.config import config
from api.util.genepanelconfig import GenepanelConfigResolver

from api.v1 import queries  # TODO: Feels strange to import something inside v1 in general util

# TEST

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import ClauseElement, Executable, literal_column
from sqlalchemy.dialects import postgresql


class CreateTempTableAs(Executable, ClauseElement):

    def __init__(self, name, query):
        self.name = name
        self.query = query.statement


@compiles(CreateTempTableAs, "postgresql")
def _create_temp_table_as(element, compiler, **kw):
    return "CREATE TEMP TABLE %s ON COMMIT DROP AS %s" % (
        element.name,
        compiler.process(element.query)
    )


###
# START SQLAlchemy support for jsonb_to_recordset
###
from sqlalchemy.sql import functions
from sqlalchemy.sql.selectable import FromClause, Alias
from sqlalchemy.sql.elements import ColumnClause
from sqlalchemy.ext.compiler import compiles


class FunctionColumn(ColumnClause):
    def __init__(self, function, name, type_=None):
        self.function = self.table = function
        self.name = self.key = name
        self.type = type_
        self.is_literal = False

    @property
    def _from_objects(self):
        return []

    def _make_proxy(self, selectable, name=None, attach=True,
                    name_is_truncatable=False, **kw):
        if self.name == self.function.name:
            name = selectable.name
        else:
            name = self.name

        co = ColumnClause(name, self.type)
        co.key = self.name
        co._proxies = [self]
        if selectable._is_clone_of is not None:
            co._is_clone_of = \
                selectable._is_clone_of.columns.get(co.key)
        co.table = selectable
        co.named_with_table = False
        if attach:
            selectable._columns[co.key] = co
        return co


@compiles(FunctionColumn)
def _compile_function_column(element, compiler, **kw):
    if kw.get('asfrom', False):
        return "(%s).%s" % (
            compiler.process(element.function, **kw),
            compiler.preparer.quote(element.name)
        )
    else:
        return element.name


class PGAlias(Alias):
    pass


@compiles(PGAlias)
def _compile_pg_alias(element, compiler, **kw):
    text = compiler.visit_alias(element, **kw)
    if kw['asfrom']:
        text += "(%s)" % (
            ", ".join(
                "%s %s" % (
                    col.name,
                    compiler.visit_typeclause(col)) for col in
                element.element.c
            )

        )
    return text


class ColumnFunction(functions.FunctionElement):
    __visit_name__ = 'function'

    @property
    def columns(self):
        return FromClause.columns.fget(self)

    def _populate_column_collection(self):
        for name, type_ in self.column_names:
            self._columns[name] = FunctionColumn(self, name, type_)

    def alias(self, name):
        return PGAlias(self, name)

###
# END OF SQLAlchemy support for jsonb_to_recordset
###


class TempAlleleFilterTable(object):
    """
    Creates a temporary table to aid AlleleFiltering.

    Use either as TempAlleleFilterTable(session, allele_ids, config).create()
    or as a context manager:

    with TempAlleleFilterTable(session, allele_ids, config) as table:
        ...

    When used as a context manager, the table is explicitly dropped at exit.
    Otherwise, it should be dropped at end of transaction.

    The returned table is a SQLAlchemy table() description of the created table.

    Table example:
    -------------------------------------------------------------------------------------------------------------------------
    | allele_id | symbol  | transcript      | exon_distance | inDB.AF | ExAC.G           | esp6500.AA | esp6500.EA | 1000g.G |
    -------------------------------------------------------------------------------------------------------------------------
    | 3         | PLOD1   | ENST00000196061 | -89           | 0.0422  | None             | None       | None       | 0.008   |
    | 3         | PLOD1   | ENST00000376369 | -89           | 0.0422  | None             | None       | None       | 0.008   |
    | 3         | PLOD1   | ENST00000465920 | None          | 0.0422  | None             | None       | None       | 0.008   |
    | 3         | PLOD1   | ENST00000470133 | None          | 0.0422  | None             | None       | None       | 0.008   |
    | 3         | PLOD1   | ENST00000485046 | None          | 0.0422  | None             | None       | None       | 0.008   |
    | 3         | PLOD1   | ENST00000491536 | None          | 0.0422  | None             | None       | None       | 0.008   |
    | 3         | PLOD1   | NM_000302.3     | -89           | 0.0422  | None             | None       | None       | 0.008   |
    | 3         | PLOD1   | XM_005263474.1  | -89           | 0.0422  | None             | None       | None       | 0.008   |
    """

    def __init__(self, session, allele_ids, config):
        self.session = session
        self.allele_ids = allele_ids
        self.config = config

    def create(self):

        frequency_groups = config['variant_criteria']['frequencies']['groups']
        freqs = list()
        for freq_group in frequency_groups:
            for freq_provider, freq_keys in frequency_groups[freq_group].iteritems():  # 'ExAC', ['G', 'SAS', ...]
                freqs += [(freq_provider, freq_key) for freq_key in freq_keys]

        class jsonb_to_recordset_func(ColumnFunction):
            name = 'jsonb_to_recordset'
            column_names = [('transcript', String()), ('symbol', String()), ('exon_distance', Integer())]

        transcript_records = jsonb_to_recordset_func(annotation.Annotation.annotations['transcripts']).alias('j')

        tmp_allele_filter_q = self.session.query(
            annotation.Annotation.allele_id,
            transcript_records.c.symbol.label('symbol'),
            transcript_records.c.transcript.label('transcript'),
            transcript_records.c.exon_distance.label('exon_distance'),
            *[annotation.Annotation.annotations[('frequencies', k, 'freq', v)].cast(Float).label(k + '.' + v) for k, v in freqs]
        ).filter(
            annotation.Annotation.allele_id.in_(allele_ids),
            annotation.Annotation.date_superceeded.is_(None)  # Important!
        ).distinct()

        self.session.execute(CreateTempTableAs('tmp_allele_filter_internal_only', tmp_allele_filter_q))

        # TODO: For some reason it goes faster without index on frequency...?
        for c in ['symbol', 'exon_distance']:
            self.session.execute('CREATE INDEX ix_tmp_allele_filter_{0} ON tmp_allele_filter_internal_only ({0})'.format(c));

        self.session.execute('ANALYZE tmp_allele_filter_internal_only')

        return table(
            'tmp_allele_filter_internal_only',
            column('allele_id', Integer),
            column('symbol', String),
            column('transcript', String),
            column('exon_distance', Integer),
            *[column(k + '.' + v, Float) for k, v in freqs]
        )

    def __enter__(self):
        return self.create()

    def __exit__(self, type, value, traceback):
        # Extra safety. Table should normally be dropped at end of transaction,
        # but even better to be explicit.
        self.session.execute('DROP TABLE IF EXISTS tmp_allele_filter_internal_only;')


class AlleleFilter(object):

    def __init__(self, session, config):

        self.session = session
        self.config = config

    def _create_freq_filter(self, af_table, genepanels, gp_symbols, threshold_func):
        """
        """
        # frequency groups tells us what should go into e.g. 'external' and 'internal' groups
        # TODO: Get from merged genepanel config when ready
        frequency_groups = config['variant_criteria']['frequencies']['groups']

        gp_filter = dict()  # {('HBOC', 'v01'): <SQLAlchemy filter>, ...}

        # TODO: Fix this mess when we improve the genepanel config
        # We shouldn't make one filter per gene, but rather one for AD, one for non-AD and then
        # one for each gene override
        for gp_key, symbols in gp_symbols.iteritems():  # loop over every genepanel, with related genes
            genepanel = next(g for g in genepanels if g.name == gp_key[0] and g.version == gp_key[1])
            gp_config_resolver = GenepanelConfigResolver(genepanel=genepanel)
            filters = list()
            for symbol in symbols:

                or_filters = list()  # Filters to be OR'ed together
                # Get symbol specific thresholds (gives us thresholds per group)
                group_thresholds = gp_config_resolver.resolve(symbol)['freq_cutoffs']
                # Next, create the filters for all the groups in group_thresholds
                for group, thresholds in group_thresholds.iteritems():  # 'external'/'internal', {'hi_freq_cutoff': 0.03, ...}}
                    if group not in frequency_groups:
                        raise RuntimeError("Group {} specified in freq_cutoffs, but it doesn't exist in configuration".format(group))
                    for freq_provider, freq_keys in frequency_groups[group].iteritems():  # 'ExAC', ['G', 'SAS', ...]
                        for freq_key in freq_keys:
                            or_filters.append(
                                threshold_func(af_table, freq_provider, freq_key, thresholds)
                            )
                    # Construct final filter for this symbol
                    # Example: af.symbol = "BRCA2" AND (af."ExAC.G" > 0.04 OR af."1000g.G" > 0.01)
                    filters.append(
                        and_(
                            af_table.c.symbol == symbol,
                            or_(
                                *or_filters
                            )
                        )
                    )
            # Construct final filter for the genepanel
            gp_filter[gp_key] = or_(*filters)
        return gp_filter

    def get_commonness_groups(self, allele_ids, genepanel_keys):
        # First get all genepanel object for the genepanels given in input
        genepanels = self.session.query(
            gene.Genepanel
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(genepanel_keys)
        ).all()

        # Get all genes for each genepanel, will be used later in query filtering
        gp_symbols_rows = self.session.query(
            gene.Genepanel.name,
            gene.Genepanel.version,
            gene.Gene.hugo_symbol
        ).join(
            gene.Genepanel.transcripts,
            gene.Gene
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(genepanel_keys)
        ).distinct().all()

        # Convert to dict {('HBOC', 'v01'): ['BRCA1', 'BRCA2', ...]}
        gp_symbols = defaultdict(list)
        for row in gp_symbols_rows:
            gp_symbols[(row[0], row[1])].append(row[2])

        with TempAlleleFilterTable(self.session, allele_ids, config) as allele_filter_tbl:

            def common_threshold(allele_filter_tbl, freq_provider, freq_key, thresholds):
                return getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) >= thresholds['hi_freq_cutoff']

            def less_common_threshold(allele_filter_tbl, freq_provider, freq_key, thresholds):
                return and_(
                    getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) < thresholds['hi_freq_cutoff'],
                    getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) >= thresholds['lo_freq_cutoff']
                )

            def below_threshold(allele_filter_tbl, freq_provider, freq_key, thresholds):
                return getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) < thresholds['lo_freq_cutoff']

            commonness_result = {
                'common': dict(),
                'less_common': dict(),
                'low_freq': dict(),
            }

            threshold_funcs = {
                'common': common_threshold,
                'less_common': less_common_threshold,
                'low_freq': below_threshold
            }

            for commonness_group, result in commonness_result.iteritems():

                gp_filters = self._create_freq_filter(
                    allele_filter_tbl,
                    genepanels,
                    gp_symbols,
                    threshold_funcs[commonness_group]
                )

                for gp_key in genepanel_keys:
                    allele_ids = self.session.query(allele_filter_tbl.c.allele_id).filter(
                        gp_filters[gp_key]
                    ).distinct().all()
                    result[gp_key] = [a[0] for a in allele_ids]

            # Invert result structure
            final_result = {k: dict() for k in gp_symbols}
            for gp_key in final_result:
                for k, v in commonness_result.iteritems():
                    final_result[gp_key][k] = v[gp_key]

            return final_result

    def filter_gene(self, allele_ids, genepanel_keys):
        pass

    def filter_intronic(self, allele_ids, genepanel_keys):
        pass

    def filter_frequency(self, allele_ids, genepanel_keys):
        # FIXME: Remember to exclude classified 3-5 from filtering...

        pass


if __name__ == '__main__':
    from vardb.util.db import DB
    db = DB()
    db.connect()

    allele_ids = db.session.query(allele.Allele.id).join(
        allele.Allele.genotypes,
        sample.Sample,
        sample.Analysis
    ).filter(
        sample.Analysis.genepanel_name == 'HBOC',
        sample.Analysis.genepanel_version == 'v01',
    ).distinct()
    print len(allele_ids.all())

    af = AlleleFilter(db.session, config)

    #filter_alleles(db.session, [1,2,3,4,5,6], [('KREFT17', 'v01'), ('HBOC', 'v01'), ('HBOCUTV', 'v01')])
    af.filter_frequency(
        allele_ids,
        [('HBOC', 'v01'), ('HBOCUTV', 'v01'), ('EEogPU', 'v02'), ('Iktyose', 'v02'), ('Joubert', 'v02'), ('Bindevev', 'v02')]
    )
