import datetime
from collections import defaultdict
from sqlalchemy import or_, and_, tuple_, func, cast, text, column, Float, String, table, Integer
from sqlalchemy.dialects.postgresql import JSONB
from vardb.datamodel import sample, workflow, assessment, allele, genotype, gene, annotation

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
            transcript_records.c.symbol.label('exon_distance'),
            *[annotation.Annotation.annotations[('frequencies', k, 'freq', v)].cast(Float).label(k + '.' + v) for k, v in freqs]
        ).filter(
            annotation.Annotation.allele_id.in_(allele_ids),
            annotation.Annotation.date_superceeded.is_(None)  # Important!
        )

        self.session.execute(CreateTempTableAs('tmp_allele_filter_internal_only', tmp_allele_filter_q))

        # TODO: For some reason it goes faster without index on frequency...?
        for c in ['symbol', 'exon_distance']:
            self.session.execute('CREATE INDEX ix_tmp_allele_filter_{0} ON tmp_allele_filter_internal_only ({0})'.format(c));

        self.session.execute('ANALYZE tmp_allele_filter_internal_only');

        return table(
            'tmp_allele_filter_internal_only',
            column('allele_id', Integer),
            column('symbol', String),
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

    FREQ_FILTER_TEMPLATE = "(a.annotations #>>'{{frequencies, {freq_provider}, freq, {freq_key}}}')::float {comparator} {threshold}"

    def __init__(self, session, config):

        self.session = session
        self.config = config

    def _create_above_threshold_filter(self, freq_provider, freq_key, thresholds):
        return AlleleFilter.FREQ_FILTER_TEMPLATE.format(
            freq_provider=freq_provider,
            freq_key=freq_key,
            comparator='>=',
            threshold=thresholds['hi_freq_cutoff']
        )

    def _create_between_threshold_filter(self, freq_provider, freq_key, thresholds):
        return '(' + \
            AlleleFilter.FREQ_FILTER_TEMPLATE.format(
                freq_provider=freq_provider,
                freq_key=freq_key,
                comparator='<',
                threshold=thresholds['hi_freq_cutoff']
            ) \
            + ' AND ' + \
            AlleleFilter.FREQ_FILTER_TEMPLATE.format(
                freq_provider=freq_provider,
                freq_key=freq_key,
                comparator='>=',
                threshold=thresholds['lo_freq_cutoff']
            ) \
            + ')'

    def _create_below_threshold_filter(self, freq_provider, freq_key, thresholds):
        return AlleleFilter.FREQ_FILTER_TEMPLATE.format(
            freq_provider=freq_provider,
            freq_key=freq_key,
            comparator='<',
            threshold=thresholds['lo_freq_cutoff']
        )

    def _create_freq_where_clause_org(self, genepanels, gp_symbols, threshold_func):
        """
        gp_symbols = {('HBOC', 'v01'): ['SYMBOL1', 'SYMBOL1', ...]}
        """

        # groups tells us what should go into e.g. 'external' and 'internal' groups
        frequency_groups = config['variant_criteria']['frequencies']['groups']

        gp_where_clauses = dict()  # {('HBOC', 'v01'): 'WHERE-clause', ...}
        for gp_key, symbols in gp_symbols.iteritems():  # loop over every genepanel, with related genes
            genepanel = next(g for g in genepanels if g.name == gp_key[0] and g.version == gp_key[1])
            gp_config_resolver = GenepanelConfigResolver(genepanel=genepanel)
            filters = list()
            for symbol in symbols:
                or_filters = list()
                # Get symbol specific thresholds (gives us thresholds per group)
                group_thresholds = gp_config_resolver.resolve(symbol)['freq_cutoffs']
                # Next, create the filters for all the groups in group_thresholds
                for group, thresholds in group_thresholds.iteritems():  # 'external'/'internal', {'hi_freq_cutoff': 0.03, ...}}
                    if group not in frequency_groups:
                        raise RuntimeError("Group {} specified in freq_cutoffs, but it doesn't exist in configuration".format(group))
                    for freq_provider, freq_keys in frequency_groups[group].iteritems():  # 'ExAC', ['G', 'SAS', ...]
                        for freq_key in freq_keys:
                            or_filters.append(
                                threshold_func(freq_provider, freq_key, thresholds)
                            )
                    filters.append(
                        "(t.symbol = '{}'".format(symbol) + ' AND (' + ' OR '.join(or_filters) + '))'
                    )
            gp_where_clauses[gp_key] = ' OR '.join(filters)
        return gp_where_clauses

    def _create_freq_where_clause3(self, genepanels, gp_symbols, threshold_func):
        """
        gp_symbols = {('HBOC', 'v01'): ['SYMBOL1', 'SYMBOL1', ...]}
        """

        # groups tells us what should go into e.g. 'external' and 'internal' groups
        frequency_groups = config['variant_criteria']['frequencies']['groups']

        gp_where_clauses = dict()  # {('HBOC', 'v01'): 'WHERE-clause', ...}
        for gp_key, symbols in gp_symbols.iteritems():  # loop over every genepanel, with related genes
            genepanel = next(g for g in genepanels if g.name == gp_key[0] and g.version == gp_key[1])
            gp_config_resolver = GenepanelConfigResolver(genepanel=genepanel)
            filters = list()
            for symbol in symbols:
                or_filters = list()
                # Get symbol specific thresholds (gives us thresholds per group)
                group_thresholds = gp_config_resolver.resolve(symbol)['freq_cutoffs']
                # Next, create the filters for all the groups in group_thresholds
                for group, thresholds in group_thresholds.iteritems():  # 'external'/'internal', {'hi_freq_cutoff': 0.03, ...}}
                    if group not in frequency_groups:
                        raise RuntimeError("Group {} specified in freq_cutoffs, but it doesn't exist in configuration".format(group))
                    for freq_provider, freq_keys in frequency_groups[group].iteritems():  # 'ExAC', ['G', 'SAS', ...]
                        for freq_key in freq_keys:
                            or_filters.append(
                                threshold_func(freq_provider, freq_key, thresholds)
                            )
                    filters.append(
                        "(a.annotations)::jsonb @> '{{\"transcripts\":[{{\"symbol\":\"{}\"}}]}}'::jsonb".format(symbol) + ' AND (' + ' OR '.join(or_filters) + ')'
                    )
            gp_where_clauses[gp_key] = ' OR '.join(filters[:50])
        return gp_where_clauses

    def _create_freq_where_clause(self, genepanels, gp_symbols, threshold_func):
        """
        gp_symbols = {('HBOC', 'v01'): ['SYMBOL1', 'SYMBOL1', ...]}
        """

        # groups tells us what should go into e.g. 'external' and 'internal' groups
        frequency_groups = config['variant_criteria']['frequencies']['groups']

        gp_where_clauses = dict()  # {('HBOC', 'v01'): 'WHERE-clause', ...}
        for gp_key, symbols in gp_symbols.iteritems():  # loop over every genepanel, with related genes
            genepanel = next(g for g in genepanels if g.name == gp_key[0] and g.version == gp_key[1])
            gp_config_resolver = GenepanelConfigResolver(genepanel=genepanel)
            filters = list()
            for symbol in symbols:
                or_filters = list()
                # Get symbol specific thresholds (gives us thresholds per group)
                group_thresholds = gp_config_resolver.resolve(symbol)['freq_cutoffs']
                # Next, create the filters for all the groups in group_thresholds
                for group, thresholds in group_thresholds.iteritems():  # 'external'/'internal', {'hi_freq_cutoff': 0.03, ...}}
                    if group not in frequency_groups:
                        raise RuntimeError("Group {} specified in freq_cutoffs, but it doesn't exist in configuration".format(group))
                    for freq_provider, freq_keys in frequency_groups[group].iteritems():  # 'ExAC', ['G', 'SAS', ...]
                        for freq_key in freq_keys:
                            or_filters.append(
                                'af."'+freq_provider + '.' + freq_key + '" > ' + str(thresholds['hi_freq_cutoff'])
                            )
                    filters.append(
                        "(af.symbol = '{}'".format(symbol) + ' AND (' + ' OR '.join(or_filters) + '))'
                    )
            gp_where_clauses[gp_key] = ' OR '.join(filters)
        return gp_where_clauses

    def filter_gene(self, allele_ids, genepanel_keys):
        pass

    def filter_intronic(self, allele_ids, genepanel_keys):
        pass

    def filter_frequency(self, allele_ids, genepanel_keys):

        import datetime
        print datetime.datetime.now().time()
        with TempAlleleFilterTable(self.session, allele_ids, config) as allele_filter_tbl:
            print datetime.datetime.now().time()

            # Filter on genepanel transcripts
            genepanel_filtered = queries.alleles_transcript_filtered_genepanel(
                self.session,
                allele_ids,
                genepanel_keys
            ).subquery()

            # First get all configs for the genepanels given in input
            genepanels = self.session.query(
                gene.Genepanel
            ).filter(
                tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(genepanel_keys)
            ).all()

            # Get all relevant gene symbols for which to query for config overrides
            # TODO: Maybe not the currect source for symbols??
            all_symbols = self.session.query(
                genepanel_filtered.c.name,
                genepanel_filtered.c.version,
                genepanel_filtered.c.annotation_symbol
            ).distinct().all()

            gp_symbols = defaultdict(list)  # {('HBOC', 'v01'): ['BRCA1', 'BRCA2', ...]}
            for a in all_symbols:
                gp_symbols[(a[0], a[1])].append(a[2])

            threshold_funcs = [
                self._create_above_threshold_filter,
                self._create_between_threshold_filter,
                self._create_below_threshold_filter,
            ]
            for threshold_func in threshold_funcs:
                gp_where_clauses = self._create_freq_where_clause(genepanels, gp_symbols, threshold_func)

                for gp_key, where_clause in gp_where_clauses.iteritems():

                    frequency_query_org = '''
                        SELECT DISTINCT ON (a.allele_id) a.allele_id
                        FROM annotation AS a
                        WHERE {}
                        '''

                    frequency_query = '''
                        SELECT DISTINCT ON (af.allele_id) af.allele_id
                        FROM tmp_allele_filter AS af
                        WHERE {}
                        '''
                    query = frequency_query.format(where_clause)
                    allele_ids = self.session.execute(query)
                    allele_ids = [a[0] for a in allele_ids]
                    print gp_key, len(allele_ids)

            import sys; sys.exit(0)



if __name__ == '__main__':
    from vardb.util.db import DB
    db = DB()
    db.connect()

    allele_ids = db.session.query(allele.Allele.id).join(
        allele.Allele.genotypes,
        sample.Sample,
        sample.Analysis
    ).filter(
        #sample.Analysis.genepanel_name == 'Bindevev',
        #sample.Analysis.genepanel_version == 'v02',
    ).distinct()
    print len(allele_ids.all())

    af = AlleleFilter(db.session, config)

    #filter_alleles(db.session, [1,2,3,4,5,6], [('KREFT17', 'v01'), ('HBOC', 'v01'), ('HBOCUTV', 'v01')])
    af.filter_frequency(
        allele_ids,
        [('Ciliopati', 'v03'), ('Bindevev', 'v02'), ('EEogPU', 'v02'), ('Iktyose', 'v02'), ('Joubert', 'v02')]
    )
