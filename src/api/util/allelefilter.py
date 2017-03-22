from collections import OrderedDict
import itertools
from sqlalchemy import or_, and_, tuple_, column, Float, String, table, Integer, func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import ClauseElement, Executable
from sqlalchemy.sql import functions
from sqlalchemy.sql.selectable import FromClause, Alias
from sqlalchemy.sql.elements import ColumnClause

from vardb.datamodel import assessment, gene, annotation

from api.util import queries
from api.util.genepanelconfig import GenepanelConfigResolver


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

        frequency_groups = self.config['variant_criteria']['frequencies']['groups']
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
            annotation.Annotation.allele_id.in_(self.allele_ids),
            annotation.Annotation.date_superceeded.is_(None)  # Important!
        )

        self.session.execute(CreateTempTableAs('tmp_allele_filter_internal_only', tmp_allele_filter_q))

        # TODO: For some reason it goes faster without index on frequency...?
        for c in ['allele_id', 'symbol', 'transcript', 'exon_distance']:
            self.session.execute('CREATE INDEX ix_tmp_allele_filter_{0} ON tmp_allele_filter_internal_only ({0})'.format(c))

        self.session.execute('ANALYZE tmp_allele_filter_internal_only')

        return table(
            'tmp_allele_filter_internal_only',
            column('allele_id', Integer),
            column('symbol', String),
            column('transcript', String),
            column('exon_distance', Integer),
            *[column(k + '.' + v, Float) for k, v in freqs]
        )

    def drop(self):
        self.session.execute('DROP TABLE IF EXISTS tmp_allele_filter_internal_only;')

    def __enter__(self):
        return self.create()

    def __exit__(self, type, value, traceback):
        # Extra safety. Table should normally be dropped at end of transaction,
        # but even better to be explicit.
        return self.drop()


class AlleleFilter(object):

    def __init__(self, session, config):

        self.session = session
        self.config = config

    def _get_AD_genes(self, gp_key):
        """
        Fetches all genes with _only_ 'AD' phenotypes.
        """
        distinct_inheritance = self.session.query(
            gene.Phenotype.genepanel_name,
            gene.Phenotype.genepanel_version,
            gene.Phenotype.gene_id,
        ).group_by(
            gene.Phenotype.genepanel_name,
            gene.Phenotype.genepanel_version,
            gene.Phenotype.gene_id
        ).having(func.count(gene.Phenotype.inheritance) == 1).subquery()

        genes = self.session.query(
            gene.Phenotype.gene_id,
        ).join(
            distinct_inheritance,
            and_(
                gene.Phenotype.genepanel_name == distinct_inheritance.c.genepanel_name,
                gene.Phenotype.genepanel_version == distinct_inheritance.c.genepanel_version,
                gene.Phenotype.gene_id == distinct_inheritance.c.gene_id
            )
        ).filter(
            gene.Phenotype.genepanel_name == gp_key[0],
            gene.Phenotype.genepanel_version == gp_key[1],
            gene.Phenotype.inheritance == 'AD'
        ).distinct().all()
        return [g[0] for g in genes]

    def _get_freq_threshold_filter(self, af_table, group_thresholds, threshold_func):
        # frequency groups tells us what should go into e.g. 'external' and 'internal' groups
        # TODO: Get from merged genepanel config when ready
        frequency_groups = self.config['variant_criteria']['frequencies']['groups']
        filters = list()
        for group, thresholds in group_thresholds.iteritems():  # 'external'/'internal', {'hi_freq_cutoff': 0.03, ...}}
            if group not in frequency_groups:
                raise RuntimeError("Group {} specified in freq_cutoffs, but it doesn't exist in configuration".format(group))
            for freq_provider, freq_keys in frequency_groups[group].iteritems():  # 'ExAC', ['G', 'SAS', ...]
                for freq_key in freq_keys:
                    filters.append(
                        threshold_func(af_table, freq_provider, freq_key, thresholds)
                    )
        return or_(*filters)

    def _create_freq_filter(self, af_table, genepanels, gp_allele_ids, threshold_func):

        gp_filter = dict()  # {('HBOC', 'v01'): <SQLAlchemy filter>, ...}

        for gp_key in gp_allele_ids:  # loop over every genepanel, with related genes

            genepanel = next(g for g in genepanels if g.name == gp_key[0] and g.version == gp_key[1])
            gp_config_resolver = GenepanelConfigResolver(
                genepanel=genepanel,
                genepanel_default=self.config['variant_criteria']['genepanel_config']
            )

            # Create the different kinds of filters
            #
            # We have three types of filters:
            # 1. Gene specific treshold overrides. Targets one gene.
            # 2. AD specific thresholds. Targets set of genes with _only_ 'AD' inheritance.
            # 3. The rest. Uses 'default' threshold, targeting all genes not in 1. and 2.

            gp_final_filter = list()

            # Gene specific filter
            # Example: af.symbol = "BRCA2" AND (af."ExAC.G" > 0.04 OR af."1000g.G" > 0.01)
            override_genes = gp_config_resolver.get_genes_with_overrides()
            for symbol in override_genes:
                symbol_group_thresholds = gp_config_resolver.resolve(symbol)['freq_cutoffs']
                gp_final_filter.append(
                    and_(
                        af_table.c.symbol == symbol,
                        self._get_freq_threshold_filter(af_table, symbol_group_thresholds, threshold_func)
                    )
                )

            # AD genes
            ad_genes = self._get_AD_genes(gp_key)
            if ad_genes:
                ad_group_thresholds = gp_config_resolver.get_AD_freq_cutoffs()
                gp_final_filter.append(
                    and_(
                        af_table.c.symbol.in_(ad_genes),
                        self._get_freq_threshold_filter(af_table, ad_group_thresholds, threshold_func)
                    )
                )

            # 'default' genes (all genes not in two above cases)
            default_group_thresholds = gp_config_resolver.get_default_freq_cutoffs()
            gp_final_filter.append(
                and_(
                    ~af_table.c.symbol.in_(override_genes + ad_genes),
                    self._get_freq_threshold_filter(af_table, default_group_thresholds, threshold_func)
                )
            )

            # Construct final filter for the genepanel
            gp_filter[gp_key] = or_(*gp_final_filter)
        return gp_filter

    def get_commonness_groups(self, gp_allele_ids, allele_filter_tbl=None):
        """
        Categorizes allele ids according to their annotation frequency
        and the thresholds in the genepanel configuration.
        There are three categories: 'common', 'less_common' and 'low_freq'.

        common:       {freq} >= 'hi_freq_cutoff'
        less_common:  'lo_freq_cutoff' >= {freq} < 'hi_freq_cutoff'
        low_freq:     {freq} < 'lo_freq_cutoff'

        :note: Allele ids with no frequencies are not excluded from the results.

        :param gp_allele_ids: {('HBOC', 'v01'): [1, 2, 3, ...], ...}
        :returns: Structure with results for the three categories.

        Example for returned data:
        {
            ('HBOC', 'v01'): {
                'common': [1, 2, ...],
                'less_common': [5, 84, ...],
                'low_freq': [13, 40, ...]
            }
        }
        """

        table_creator = None
        if allele_filter_tbl is None:
            all_allele_ids = list(itertools.chain.from_iterable(gp_allele_ids.values()))
            table_creator = TempAlleleFilterTable(self.session, all_allele_ids, self.config)
            allele_filter_tbl = table_creator.create()

        # First get all genepanel object for the genepanels given in input
        genepanels = self.session.query(
            gene.Genepanel
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(gp_allele_ids.keys())
        ).all()

        def common_threshold(allele_filter_tbl, freq_provider, freq_key, thresholds):
            return getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) >= thresholds['hi_freq_cutoff']

        def less_common_threshold(allele_filter_tbl, freq_provider, freq_key, thresholds):
            return and_(
                getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) < thresholds['hi_freq_cutoff'],
                getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) >= thresholds['lo_freq_cutoff']
            )

        def low_freq_threshold(allele_filter_tbl, freq_provider, freq_key, thresholds):
            return getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) < thresholds['lo_freq_cutoff']

        commonness_result = OrderedDict([  # Ordered to get final_result correct
            ('common', dict()),
            ('less_common', dict()),
            ('low_freq', dict())
        ])

        threshold_funcs = {
            'common': common_threshold,
            'less_common': less_common_threshold,
            'low_freq': low_freq_threshold
        }

        for commonness_group, result in commonness_result.iteritems():

            # Create query filter this genepanel
            gp_filters = self._create_freq_filter(
                allele_filter_tbl,
                genepanels,
                gp_allele_ids,
                threshold_funcs[commonness_group]
            )

            for gp_key, al_ids in gp_allele_ids.iteritems():
                assert all(isinstance(a, int) for a in al_ids)
                allele_ids = self.session.query(allele_filter_tbl.c.allele_id).filter(
                    gp_filters[gp_key],
                    allele_filter_tbl.c.allele_id.in_(al_ids)
                ).distinct()
                result[gp_key] = [a[0] for a in allele_ids.all()]

        # Create final result structure.
        # The database queries can place one allele id as part of many groups,
        # but we'd like to place each in the highest group only.
        final_result = {k: dict() for k in gp_allele_ids}
        for gp_key in final_result:
            added_thus_far = set()
            for k, v in commonness_result.iteritems():
                final_result[gp_key][k] = [aid for aid in v[gp_key] if aid not in added_thus_far]
                added_thus_far.update(set(v[gp_key]))
            # Add all not part of the groups to a 'null_freq' group
            final_result[gp_key]['null_freq'] = [aid for aid in gp_allele_ids[gp_key] if aid not in added_thus_far]

        if table_creator is not None:
            table_creator.drop()

        return final_result

    def exclude_classification_allele_ids(self, allele_ids):
        """
        For each allele_id in input list, checks whether there exists
        a current classification among the ones marked
        'exclude_filtering_existing_assessment' in  config.

        If true, exclude the allele_id from the returned list.
        The use case is to avoid including alleles with classifications
        in the filtering process.
        """

        options = self.config['classification']['options']
        exclude_for_class = [o['value'] for o in options if o.get('exclude_filtering_existing_assessment')]

        to_exclude = list()

        if allele_ids:
            to_exclude = self.session.query(assessment.AlleleAssessment.allele_id).filter(
                assessment.AlleleAssessment.classification.in_(exclude_for_class),
                assessment.AlleleAssessment.allele_id.in_(allele_ids),
                assessment.AlleleAssessment.date_superceeded.is_(None)
            ).all()
            to_exclude = [t[0] for t in to_exclude]

        return [a for a in allele_ids if a not in to_exclude]

    def filtered_gene(self, gp_allele_ids, allele_filter_tbl=None):
        """
        Filters allele ids from input based on gene.

        The filtering will happen according to the genepanel's specified
        configuration, specifying what genes that should be excluded.

        If any alleles have an existing classification according to config
        'exclude_filtering_existing_assessment', they will be excluded from the
        result.

        :param gp_allele_ids: Dict of genepanel key with corresponding allele_ids {('HBOC', 'v01'): [1, 2, 3])}
        :returns: Structure similar to input, but only containing allele ids are excluded based on gene.

        :note: The returned values are allele ids that were _filtered out_
        based on gene, i.e. they are in excluded list.
        """

        # If user didn't pass cached table, create one
        table_creator = None
        if allele_filter_tbl is None:
            all_allele_ids = list(itertools.chain.from_iterable(gp_allele_ids.values()))
            table_creator = TempAlleleFilterTable(self.session, all_allele_ids, self.config)
            allele_filter_tbl = table_creator.create()

        exclude_genes = self.config['variant_criteria']['exclude_genes']

        gene_filtered = dict()
        for gp_key, allele_ids in gp_allele_ids.iteritems():
            gene_filtered_q = self.session.query(
                allele_filter_tbl.c.allele_id
            ).filter(
                allele_filter_tbl.c.symbol.in_(exclude_genes),
                allele_filter_tbl.c.allele_id.in_(allele_ids)
            ).distinct()

            gene_filtered[gp_key] = [a[0] for a in gene_filtered_q.all()]

        # Remove the ones with existing classification
        for gp_key, allele_ids in gene_filtered.iteritems():
            gene_filtered[gp_key] = self.exclude_classification_allele_ids(allele_ids)

        if table_creator:
            table_creator.drop()

        return gene_filtered

    def filtered_intronic(self, gp_allele_ids, allele_filter_tbl=None):
        """
        Filters allele ids from input based on their distance to nearest
        exon edge.

        The filtering will happen according to the genepanel's specified
        configuration, specifying what exon_distance defines intronic status.

        If any alleles have an existing classification according to config
        'exclude_filtering_existing_assessment', they will be excluded from the
        result.

        :param gp_allele_ids: Dict of genepanel key with corresponding allele_ids {('HBOC', 'v01'): [1, 2, 3])}
        :returns: Structure similar to input, but only containing allele ids that are intronic.

        :note: The returned values are allele ids that were _filtered out_
        based on intronic status, i.e. they are intronic.
        """

        all_allele_ids = list(itertools.chain.from_iterable(gp_allele_ids.values()))

        table_creator = None
        if allele_filter_tbl is None:
            table_creator = TempAlleleFilterTable(self.session, all_allele_ids, self.config)
            allele_filter_tbl = table_creator.create()

        all_gp_keys = gp_allele_ids.keys()

        filtered_transcripts = queries.alleles_transcript_filtered_genepanel(
            self.session,
            all_allele_ids,
            all_gp_keys
        ).subquery()

        intronic_region = self.config['variant_criteria']['intronic_region']

        # TODO: Add support for per gene/genepanel configuration when ready.
        intronic_filtered = dict()
        for gp_key, allele_ids in gp_allele_ids.iteritems():
            intronic_filtered_q = self.session.query(
                allele_filter_tbl.c.allele_id
            ).join(
                filtered_transcripts,
                allele_filter_tbl.c.transcript == filtered_transcripts.c.annotation_transcript
            ).filter(
                tuple_(filtered_transcripts.c.name, filtered_transcripts.c.version) == gp_key,
                or_(
                    allele_filter_tbl.c.exon_distance < intronic_region[0],
                    allele_filter_tbl.c.exon_distance > intronic_region[1]
                ),
                allele_filter_tbl.c.allele_id.in_(allele_ids)
            ).distinct()

            intronic_filtered[gp_key] = [a[0] for a in intronic_filtered_q.all()]

        # Remove the ones with existing classification
        for gp_key, allele_ids in intronic_filtered.iteritems():
            intronic_filtered[gp_key] = self.exclude_classification_allele_ids(allele_ids)

        if table_creator is not None:
            table_creator.drop()

        return intronic_filtered

    def filtered_frequency(self, gp_allele_ids, allele_filter_tbl=None):
        """
        Filters allele ids from input based on their frequency.

        The filtering will happen according to the genepanel's specified
        configuration.

        If any alleles have an existing classification according to config
        'exclude_filtering_existing_assessment', they will be excluded from the
        result.

        :param gp_allele_ids: Dict of genepanel key with corresponding allele_ids {('HBOC', 'v01'): [1, 2, 3])}
        :returns: Structure similar to input, but only containing allele ids that have high frequency.

        :note: The returned values are allele ids that were _filtered out_
        based on frequency, i.e. they have a high frequency value, not the ones
        that should be included.
        """

        table_creator = None
        if allele_filter_tbl is None:
            all_allele_ids = list(itertools.chain.from_iterable(gp_allele_ids.values()))
            table_creator = TempAlleleFilterTable(self.session, all_allele_ids, self.config)
            allele_filter_tbl = table_creator.create()

        commonness_result = self.get_commonness_groups(gp_allele_ids, allele_filter_tbl)
        frequency_filtered = dict()
        for gp_key, commonness_group in commonness_result.iteritems():
            frequency_filtered[gp_key] = self.exclude_classification_allele_ids(commonness_group['common'])

        if table_creator:
            table_creator.drop()

        return frequency_filtered

    def filter_alleles(self, gp_allele_ids):

        result = dict()
        all_allele_ids = list(itertools.chain.from_iterable(gp_allele_ids.values()))
        with TempAlleleFilterTable(self.session, all_allele_ids, self.config) as allele_filter_tbl:
            filtered_gene = self.filtered_gene(gp_allele_ids, allele_filter_tbl=allele_filter_tbl)
            filtered_frequency = self.filtered_frequency(gp_allele_ids, allele_filter_tbl=allele_filter_tbl)
            filtered_intronic = self.filtered_intronic(gp_allele_ids, allele_filter_tbl=allele_filter_tbl)

        for gp_key in gp_allele_ids:
            gp_filtered_gene = filtered_gene[gp_key]
            gp_filtered_frequency = [i for i in filtered_frequency[gp_key] if i not in gp_filtered_gene]
            excluded = gp_filtered_gene + gp_filtered_frequency
            gp_filtered_intronic = [i for i in filtered_intronic[gp_key] if i not in excluded]
            excluded = excluded + gp_filtered_intronic
            # Subtract the ones we excluded to get the ones not filtred out
            not_filtered = list(set(gp_allele_ids[gp_key]) - set(excluded))
            result[gp_key] = {
                'allele_ids': not_filtered,
                'excluded_allele_ids': {
                    'gene': gp_filtered_gene,
                    'intronic': gp_filtered_intronic,
                    'frequency': gp_filtered_frequency
                }
            }

        return result