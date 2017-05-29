from collections import OrderedDict, defaultdict
import itertools
from sqlalchemy import or_, and_, tuple_, column, Float, String, table, Integer, func, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import ClauseElement, Executable
from sqlalchemy.sql import functions
from sqlalchemy.sql.selectable import FromClause, Alias
from sqlalchemy.sql.elements import ColumnClause
from sqlalchemy.dialects.postgresql import JSONB

from api.config import config as global_genepanel_default
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
    Otherwise, it will automatically be dropped at end of transaction.

    The returned table is a SQLAlchemy table() description of the created table.

    Table example:
    -------------------------------------------------------------------------------------------------------------------
    | allele_id | symbol        | transcript      | exon_distance | inDB.AF | GNOMAD_GENOMES.G  | GNOMAD_GENOMES_num.G |
    -------------------------------------------------------------------------------------------------------------------
    | 1         | NPHP4         | XM_005263443.1  | 41            | 0.6456  | 0.645135047185    | 30730                |
    | 1         | NPHP4         | ENST00000378169 | None          | 0.6456  | 0.645135047185    | 30730                |
    | 1         | NPHP4         | NM_015102.3     | 41            | 0.6456  | 0.645135047185    | 30730                |
    | 1         | NPHP4         | ENST00000478423 | 41            | 0.6456  | 0.645135047185    | 30730                |
    | 1         | NPHP4         | XR_244787.1     | None          | 0.6456  | 0.645135047185    | 30730                |
    | 1         | NPHP4         | XM_005263445.1  | 41            | 0.6456  | 0.645135047185    | 30730                |
    """

    def __init__(self, session, allele_ids, config):
        self.session = session
        self.allele_ids = allele_ids
        self.config = config

    def get_freq_columns(self):
        """
        Creates SQLAlchemy column queries for the frequency groups specified in config.
        """
        frequency_groups = self.config['variant_criteria']['frequencies']['groups']
        freqs = list()
        for freq_group in frequency_groups:
            for freq_provider, freq_keys in frequency_groups[freq_group].iteritems():  # 'ExAC', ['G', 'SAS', ...]
                freqs += [(freq_provider, freq_key) for freq_key in freq_keys]

        columns = [column(k + '.' + v, Float) for k, v in freqs]
        column_queries = [annotation.Annotation.annotations[('frequencies', k, 'freq', v)].cast(Float).label(k + '.' + v) for k, v in freqs]
        return columns, column_queries

    def get_freq_num_threshold_columns(self):
        """
        Creates SQLAlchemy column queries for the frequency number thresholds specified in config.
        """
        config_thresholds = self.config['variant_criteria']['freq_num_thresholds']
        column_queries = list()
        columns = list()
        for freq_provider, freq_thresholds in config_thresholds.iteritems():  # 'ExAC', {'G': 2000, ...}
            column_queries += [annotation.Annotation.annotations[('frequencies', freq_provider, 'num', freq_key)].cast(Integer).label(freq_provider + '_num.' + freq_key) for freq_key in freq_thresholds]
            columns += [column(freq_provider + '_num.' + freq_key, Integer) for freq_key in freq_thresholds]

        return columns, column_queries

    def create_transcript(self):
        class jsonb_to_recordset_func(ColumnFunction):
            name = 'jsonb_to_recordset'
            column_names = [('transcript', String()), ('symbol', String()), ('exon_distance', Integer())]

        transcript_records = jsonb_to_recordset_func(annotation.Annotation.annotations['transcripts']).alias('j')

        tmp_allele_filter_transcripts_q = self.session.query(
            annotation.Annotation.allele_id,
            transcript_records.c.symbol.label('symbol'),
            transcript_records.c.transcript.label('transcript'),
            transcript_records.c.exon_distance.label('exon_distance'),
        ).filter(
            annotation.Annotation.allele_id.in_(self.allele_ids),
            annotation.Annotation.date_superceeded.is_(None)  # Important!
        )

        res = self.session.execute(CreateTempTableAs('tmp_allele_filter_transcript_internal_only', tmp_allele_filter_transcripts_q))

        # Create index if resulting table is of sufficient size
        if res.rowcount > 1000:
            for c in ["allele_id", "symbol", "transcript", "exon_distance"]:
                self.session.execute('CREATE INDEX ix_tmp_allele_filter_transcripts_{0} ON tmp_allele_filter_transcript_internal_only ({0})'.format(c))

        self.session.execute('ANALYZE tmp_allele_filter_transcript_internal_only')

        return table(
            'tmp_allele_filter_transcript_internal_only',
            column('allele_id', Integer),
            column('symbol', String),
            column('transcript', String),
            column('exon_distance', Integer),
        )

    def create_frequency(self):

        freq_columns, freq_column_queries = self.get_freq_columns()
        freq_num_columns, freq_num_column_queries = self.get_freq_num_threshold_columns()

        column_queries = freq_column_queries + freq_num_column_queries

        tmp_allele_filter_freq_q = self.session.query(
            annotation.Annotation.allele_id,
            *column_queries
        ).filter(
            annotation.Annotation.allele_id.in_(self.allele_ids),
            annotation.Annotation.date_superceeded.is_(None)  # Important!
        )

        res = self.session.execute(CreateTempTableAs('tmp_allele_filter_frequency_internal_only', tmp_allele_filter_freq_q))

        # Create index if resulting table is of sufficient size
        if res.rowcount > 1000:
            for c in freq_columns:
                c_name = str(c).replace('"', '').replace('.', '_')
                c = str(c)
                self.session.execute('CREATE INDEX ix_tmp_allele_filter_frequency_{0} ON tmp_allele_filter_frequency_internal_only ({1})'.format(c_name, c))

        self.session.execute('ANALYZE tmp_allele_filter_frequency_internal_only')

        columns = freq_columns + freq_num_columns
        return table(
            'tmp_allele_filter_frequency_internal_only',
            column('allele_id', Integer),
            *columns
        )

    def create(self):
        # Create separate temporary tables for transcript data and frequency data
        tmp_allele_filter_transcript_tbl = self.create_transcript()
        tmp_allele_filter_frequency_tbl = self.create_frequency()
        all_columns = list(tmp_allele_filter_transcript_tbl.c)+list(tmp_allele_filter_frequency_tbl.c)[1:]

        # Join the two temporary tables on allele id
        tmp_allele_filter_q = self.session.query(
            *all_columns
        ).filter(
            tmp_allele_filter_transcript_tbl.c.allele_id == tmp_allele_filter_frequency_tbl.c.allele_id
        )

        self.session.execute(CreateTempTableAs('tmp_allele_filter_internal_only', tmp_allele_filter_q))

        # TODO: For some reason it goes faster without index on frequency...?
        for c in ['allele_id', 'symbol', 'transcript', 'exon_distance']:
            self.session.execute('CREATE INDEX ix_tmp_allele_filter_{0} ON tmp_allele_filter_internal_only ({0})'.format(c))

        self.session.execute('ANALYZE tmp_allele_filter_internal_only')

        # Drop intermediate tables
        self.session.execute('DROP TABLE IF EXISTS tmp_allele_filter_frequency_internal_only;')
        self.session.execute('DROP TABLE IF EXISTS tmp_allele_filter_transcript_internal_only;')

        return table(
            'tmp_allele_filter_internal_only',
            *all_columns
        )

    def drop(self):
        self.session.execute('DROP TABLE IF EXISTS tmp_allele_filter_internal_only;')
        self.session.execute('DROP TABLE IF EXISTS tmp_allele_filter_frequency_internal_only;')
        self.session.execute('DROP TABLE IF EXISTS tmp_allele_filter_transcript_internal_only;')

    def __enter__(self):
        return self.create()

    def __exit__(self, type, value, traceback):
        # Extra safety. Tables should normally be dropped at end of transaction,
        # but even better to be explicit.
        return self.drop()


class AlleleFilter(object):

    def __init__(self, session, global_config=None):
        """
        :param session:
        :param global_config: only set when testing. Else the global config in api/config.py is used
        """
        self.session = session
        self.global_config = global_genepanel_default if not global_config else global_config


    @staticmethod
    def _get_freq_num_threshold_filter(allele_filter_tbl, provider_numbers, freq_provider, freq_key):
        """
        Check whether we have a 'num' threshold in config for given freq_provider and freq_key (e.g. ExAC->G).
        If it's defined, the num column in allelefilter table must be greater or equal to the threshold.
        """

        if freq_provider in provider_numbers and freq_key in provider_numbers[freq_provider]:
            num_threshold = provider_numbers[freq_provider][freq_key]
            assert isinstance(num_threshold, int), 'Provided frequency num threshold is not an integer'
            # num column is defined in allelefilter table as e.g. ExAC_num.G
            return getattr(allele_filter_tbl.c, freq_provider + '_num.' + freq_key) >= num_threshold

        return None

    def _get_freq_threshold_filter(self, af_table, group_thresholds, threshold_func, combine_func):
        # frequency groups tells us what should go into e.g. 'external' and 'internal' groups
        frequency_groups = self.global_config['variant_criteria']['frequencies']['groups']
        frequency_provider_numbers = self.global_config['variant_criteria']['freq_num_thresholds']

        filters = list()
        for group, thresholds in group_thresholds.iteritems():  # 'external'/'internal', {'hi_freq_cutoff': 0.03, ...}}
            if group not in frequency_groups:
                raise RuntimeError("Group {} specified in freq_cutoffs, but it doesn't exist in configuration".format(group))

            for freq_provider, freq_keys in frequency_groups[group].iteritems():  # 'ExAC', ['G', 'SAS', ...]
                for freq_key in freq_keys:
                    filters.append(
                        threshold_func(af_table, frequency_provider_numbers, freq_provider, freq_key, thresholds)
                    )

        return combine_func(*filters)

    def _common_threshold(self, allele_filter_tbl, provider_numbers, freq_provider, freq_key, thresholds):
        """
        Creates SQLAlchemy filter for common threshold for a single frequency provider and key.
        Example: ExAG.G > hi_freq_cutoff
        """
        freq_key_filters = list()
        num_filter = AlleleFilter._get_freq_num_threshold_filter(allele_filter_tbl, provider_numbers, freq_provider, freq_key)
        if num_filter is not None:
            freq_key_filters.append(num_filter)

        freq_key_filters.append(
            getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) >= thresholds['hi_freq_cutoff']
        )

        return and_(*freq_key_filters)

    def _less_common_threshold(self, allele_filter_tbl, provider_numbers, freq_provider, freq_key, thresholds):
        """
        Creates SQLAlchemy filter for less_common threshold for a single frequency provider and key.
        Example: ExAG.G < hi_freq_cutoff AND ExAG.G >= lo_freq_cutoff
        """
        freq_key_filters = list()
        num_filter = AlleleFilter._get_freq_num_threshold_filter(allele_filter_tbl, provider_numbers, freq_provider, freq_key)
        if num_filter is not None:
            freq_key_filters.append(num_filter)

        freq_key_filters.append(
            and_(
                getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) < thresholds['hi_freq_cutoff'],
                getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) >= thresholds['lo_freq_cutoff']
            )
        )

        return and_(*freq_key_filters)

    def _low_freq_threshold(self, allele_filter_tbl, provider_numbers, freq_provider, freq_key, thresholds):
        """
        Creates SQLAlchemy filter for low_freq threshold for a single frequency provider and key.
        Example: ExAG.G < lo_freq_cutoff
        """
        freq_key_filters = list()
        num_filter = AlleleFilter._get_freq_num_threshold_filter(allele_filter_tbl, provider_numbers, freq_provider, freq_key)
        if num_filter is not None:
            freq_key_filters.append(num_filter)
        freq_key_filters.append(
            getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key) < thresholds['lo_freq_cutoff']
        )

        return and_(*freq_key_filters)

    @staticmethod
    def _is_freq_null(allele_filter_tbl, threshhold_config, freq_provider, freq_key, thresholds):
        """
        Creates SQLAlchemy filter for checking whether frequency is null for a single frequency provider and key.
        Example: ExAG.G IS NULL

        :note: Function signature is same as other threshold filters in order for them to be called dynamically.
        """
        return getattr(allele_filter_tbl.c, freq_provider + '.' + freq_key).is_(None)

    def _get_AD_genes(self, gp_key):
        result = queries.ad_genes_for_genepanel(
            self.session, gp_key[0], gp_key[1]
        ).all()
        return [r[0] for r in result]


    def _create_freq_filter(self, af_table, genepanels, gp_allele_ids, threshold_func, combine_func):

        gp_filter = dict()  # {('HBOC', 'v01'): <SQLAlchemy filter>, ...}

        for gp_key in gp_allele_ids:  # loop over every genepanel, with related genes

            genepanel = next(g for g in genepanels if g.name == gp_key[0] and g.version == gp_key[1])
            gp_config_resolver = GenepanelConfigResolver(
                genepanel=genepanel,
                genepanel_default=self.global_config['variant_criteria']['genepanel_config']
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
                # Get merged genepanel for this gene/symbol
                symbol_group_thresholds = gp_config_resolver.resolve(symbol)['freq_cutoffs']
                gp_final_filter.append(
                    and_(
                        af_table.c.symbol == symbol,
                        self._get_freq_threshold_filter(af_table,
                                                        symbol_group_thresholds,
                                                        threshold_func,
                                                        combine_func)
                    )
                )

            # AD genes
            ad_genes = self._get_AD_genes(gp_key)
            if ad_genes:
                ad_group_thresholds = gp_config_resolver.get_AD_freq_cutoffs()
                gp_final_filter.append(
                    and_(
                        ~af_table.c.symbol.in_(override_genes),
                        af_table.c.symbol.in_(ad_genes),
<<<<<<< 3ebb68cbb1b4f6c737de605c6c753544156356f2
                        self._get_freq_threshold_filter(af_table,
                                                        ad_group_thresholds,
                                                        threshold_func,
                                                        combine_func)
=======
                        ~af_table.c.symbol.in_(override_genes),  # Exclude already overriden genes
                        self._get_freq_threshold_filter(af_table, genepanel_config, ad_group_thresholds, threshold_func, combine_func)
>>>>>>> [api] Fix "bug" in allelefilter where overridden gene wasn't excluded
                    )
                )

            # 'default' genes (all genes not in two above cases)
            default_group_thresholds = gp_config_resolver.get_default_freq_cutoffs()
            gp_final_filter.append(
                and_(
                    ~af_table.c.symbol.in_(override_genes + ad_genes),
                    self._get_freq_threshold_filter(af_table,
                                                    default_group_thresholds,
                                                    threshold_func,
                                                    combine_func)
                )
            )

            # Construct final filter for the genepanel
            gp_filter[gp_key] = or_(*gp_final_filter)
        return gp_filter

    def get_commonness_groups(self, gp_allele_ids, common_only=False, allele_filter_tbl=None):
        """
        Categorizes allele ids according to their annotation frequency
        and the thresholds in the genepanel configuration.
        There are five categories:
            'common', 'less_common', 'low_freq', 'null_freq' and 'num_threshold'.

        common:       {freq} >= 'hi_freq_cutoff'
        less_common:  'lo_freq_cutoff' >= {freq} < 'hi_freq_cutoff'
        low_freq:     {freq} < 'lo_freq_cutoff'
        null_freq:     All {freq} == null
        num_threshold: Not part of above groups, and below 'num' threshold for all relevant {freq}

        :note: Allele ids with no frequencies are not excluded from the results.

        :param gp_allele_ids: {('HBOC', 'v01'): [1, 2, 3, ...], ...}
        :param common_only: Whether to only check for 'common' group. Use when you only need the common group, as it's faster.
        :returns: Structure with results for the three categories.

        Example for returned data:
        {
            ('HBOC', 'v01'): {
                'common': [1, 2, ...],
                'less_common': [5, 84, ...],
                'low_freq': [13, 40, ...],
                'null_freq': [14, 34, ...],
                'num_threshold': [50],
            }
        }
        """

        table_creator = None
        if allele_filter_tbl is None:
            all_allele_ids = list(itertools.chain.from_iterable(gp_allele_ids.values()))
            table_creator = TempAlleleFilterTable(self.session, all_allele_ids, self.global_config)
            allele_filter_tbl = table_creator.create()

        # First get all genepanel object for the genepanels given in input
        genepanels = self.session.query(
            gene.Genepanel
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(gp_allele_ids.keys())
        ).all()

        commonness_entries = [
            ('common', dict()),
        ]
        if not common_only:
            commonness_entries += [
                ('less_common', dict()),
                ('low_freq', dict()),
                ('null_freq', dict())
            ]
        commonness_result = OrderedDict(commonness_entries)  # Ordered to get final_result processing correct later

        threshold_funcs = {
            'common': (self._common_threshold, or_),
            'less_common': (self._less_common_threshold, or_),
            'low_freq': (self._low_freq_threshold, or_),
            'null_freq': (self._is_freq_null, and_)
        }

        for commonness_group, result in commonness_result.iteritems():

            # Create query filter this genepanel
            gp_filters = self._create_freq_filter(
                allele_filter_tbl,
                genepanels,
                gp_allele_ids,
                threshold_funcs[commonness_group][0],
                combine_func=threshold_funcs[commonness_group][1]
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

            if not common_only:
                # Add all not part of the groups to a 'num_threshold' group,
                # since they must have missed freq num threshold
                final_result[gp_key]['num_threshold'] = [aid for aid in gp_allele_ids[gp_key] if aid not in added_thus_far]

        if table_creator is not None:
            table_creator.drop()

        return final_result

    def remove_alleles_with_classification(self, allele_ids):
        """
        Return the allele ids that have have an existing classification according with
        global config ['classification']['options']

        Reason: alleles with classification should be displayed to the user.

        """

        options = self.global_config['classification']['options']
        exclude_for_class = [o['value'] for o in options if o.get('exclude_filtering_existing_assessment')]

        with_classification = list()

        if allele_ids:
            with_classification = self.session.query(assessment.AlleleAssessment.allele_id).filter(
                assessment.AlleleAssessment.classification.in_(exclude_for_class),
                assessment.AlleleAssessment.allele_id.in_(allele_ids),
                assessment.AlleleAssessment.date_superceeded.is_(None)
            ).all()
            with_classification = [t[0] for t in with_classification]

        return filter(lambda i: i not in with_classification, allele_ids)

    def filtered_gene(self, gp_allele_ids, allele_filter_tbl=None):
        """
        Only return the allele IDs whose gene symbol are configured to be excluded.

        Currently this is not configured, as exclusion is built into the pipeline
        producing variants to ella.
        """

        gene_filtered = dict()
        for gp_key, _ in gp_allele_ids.iteritems():
            gene_filtered[gp_key] = list()  # no alleles are filtered away based on gene symbol only

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
            table_creator = TempAlleleFilterTable(self.session, all_allele_ids, self.global_config)
            allele_filter_tbl = table_creator.create()

        all_gp_keys = gp_allele_ids.keys()

        filtered_transcripts = queries.alleles_transcript_filtered_genepanel(
            self.session,
            all_allele_ids,
            all_gp_keys,
            self.global_config.get("transcripts", {}).get("inclusion_regex")
        ).subquery()

        intronic_region = self.global_config['variant_criteria']['intronic_region']

        intronic_filtered = dict()
        all_alleles_q = self.session.query(
            allele_filter_tbl.c.allele_id,
            allele_filter_tbl.c.exon_distance,
            allele_filter_tbl.c.transcript,
        ).join(
            filtered_transcripts,
            allele_filter_tbl.c.transcript == filtered_transcripts.c.annotation_transcript
        )
        for gp_key, allele_ids in gp_allele_ids.iteritems():
            # Determine which allele ids are in an exon (with exon_distance == None, or within intronic_region)
            exonic_alleles_q = all_alleles_q.filter(
                tuple_(filtered_transcripts.c.name, filtered_transcripts.c.version) == gp_key,
                or_(
                    allele_filter_tbl.c.exon_distance.is_(None),
                    or_(
                        and_(
                            allele_filter_tbl.c.exon_distance >= intronic_region[0],
                            allele_filter_tbl.c.exon_distance < intronic_region[1],
                        ),
                        and_(
                            allele_filter_tbl.c.exon_distance < intronic_region[1],
                            allele_filter_tbl.c.exon_distance >= intronic_region[0],
                        )
                    )
                ),
                allele_filter_tbl.c.allele_id.in_(allele_ids)
            ).distinct()

            exonic_allele_ids = [a[0] for a in exonic_alleles_q.all()]
            non_exonic_allele_ids = list(set(allele_ids) - set(exonic_allele_ids))

            # Filter the intronic allele ids outside the specified intronic region
            intronic_filtered_q = all_alleles_q.filter(
                tuple_(filtered_transcripts.c.name, filtered_transcripts.c.version) == gp_key,
                or_(
                    allele_filter_tbl.c.exon_distance < intronic_region[0],
                    allele_filter_tbl.c.exon_distance > intronic_region[1]
                ),
                allele_filter_tbl.c.allele_id.in_(non_exonic_allele_ids)
            ).distinct()

            intronic_filtered[gp_key] = list(set([a[0] for a in intronic_filtered_q.all()]))

        # Remove the ones with existing classification
        for gp_key, allele_ids in intronic_filtered.iteritems():
            intronic_filtered[gp_key] = self.remove_alleles_with_classification(allele_ids)

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
            table_creator = TempAlleleFilterTable(self.session, all_allele_ids, self.global_config)
            allele_filter_tbl = table_creator.create()

        commonness_result = self.get_commonness_groups(gp_allele_ids, common_only=True, allele_filter_tbl=allele_filter_tbl)
        frequency_filtered = dict()

        for gp_key, commonness_group in commonness_result.iteritems():
            frequency_filtered[gp_key] = self.remove_alleles_with_classification(commonness_group['common'])

        if table_creator:
            table_creator.drop()

        return frequency_filtered

    def filter_utr(self, gp_key, allele_ids):
        """
        Filters out variants that have worst consequence equal to 3_prime_UTR_variant or 5_prime_UTR_variant in any
        of the annotation transcripts included.
        :param gp_key: (genepanel_name, genepanel_version) used for extracting transcripts
        :param allele_ids: allele_ids to run filter on
        :return: allele ids to be filtered out
        """

        consequences_ordered = self.global_config["transcripts"].get("consequences")

        # An ordering of consequences has not been specified, return empty list
        if consequences_ordered is None:
            return []

        # Also return empty list if *_prime_UTR_variant is not specified in consequences_ordered
        if not ('3_prime_UTR_variant' in consequences_ordered and '5_prime_UTR_variant' in consequences_ordered):
            return []

        utr_consequence_index = min([consequences_ordered.index(c) for c in ['3_prime_UTR_variant', '5_prime_UTR_variant']])

        class jsonb_to_recordset_func(ColumnFunction):
            name = 'jsonb_to_recordset'
            column_names = [('consequences', JSONB()), ('transcript', String())]

        transcript_records = jsonb_to_recordset_func(annotation.Annotation.annotations['transcripts']).alias('j')

        # Get transcripts to be included for this genepanel
        inclusion_regex = self.global_config.get("transcripts", {}).get("inclusion_regex")
        filtered_transcripts = queries.alleles_transcript_filtered_genepanel(self.session, allele_ids, [gp_key], inclusion_regex).subquery()

        # Fetch the consequences for each allele (several lines per allele id)
        allele_id_consequences = self.session.query(
            annotation.Annotation.allele_id,
            transcript_records.c.transcript.label('transcript'),
            transcript_records.c.consequences.label('consequences'),
        ).filter(
            annotation.Annotation.allele_id == filtered_transcripts.c.allele_id,
            transcript_records.c.transcript == filtered_transcripts.c.annotation_transcript,
            annotation.Annotation.date_superceeded.is_(None)  # Important!
        ).all()

        # Concatenate all consequences for each allele id
        allele_consequences = defaultdict(list)
        for allele_id, transcript, consequences in allele_id_consequences:
            if consequences is None:
                allele_consequences[allele_id] += [None]
            else:
                allele_consequences[allele_id] += consequences

        def get_consequence_index(consequences):
            return map(lambda c: consequences_ordered.index(c) if c in consequences_ordered else -1, consequences)

        # Check if it has consequence 3_prime_UTR_variant/5_prime_UTR_variant, and if so, if this is the worst consequence
        utr_filtered = []
        for allele_id, consequences in allele_consequences.iteritems():
            if '3_prime_UTR_variant' in consequences or '5_prime_UTR_variant' in consequences:
                worst_consequence_index = min(get_consequence_index(consequences))
                if worst_consequence_index >= utr_consequence_index:
                    utr_filtered.append(allele_id)

        # Remove the ones with existing classification
        utr_filtered = self.remove_alleles_with_classification(utr_filtered)

        return utr_filtered

    def filter_alleles(self, gp_allele_ids):
        result = dict()
        all_allele_ids = list(itertools.chain.from_iterable(gp_allele_ids.values()))
        with TempAlleleFilterTable(self.session, all_allele_ids, self.global_config) as allele_filter_tbl:
            filtered_gene = self.filtered_gene(gp_allele_ids, allele_filter_tbl=allele_filter_tbl)
            filtered_frequency = self.filtered_frequency(gp_allele_ids, allele_filter_tbl=allele_filter_tbl)
            filtered_intronic = self.filtered_intronic(gp_allele_ids, allele_filter_tbl=allele_filter_tbl)

        for gp_key in gp_allele_ids:
            gp_filtered_gene = filtered_gene[gp_key]
            gp_filtered_frequency = [i for i in filtered_frequency[gp_key] if i not in gp_filtered_gene]
            excluded = gp_filtered_gene + gp_filtered_frequency
            gp_filtered_intronic = [i for i in filtered_intronic[gp_key] if i not in excluded]
            excluded = excluded + gp_filtered_intronic

            # Subtract the ones we excluded to get the ones not filtered out
            not_filtered = list(set(gp_allele_ids[gp_key]) - set(excluded))

            filtered_utr = self.filter_utr(gp_key, not_filtered)
            not_filtered = list(set(not_filtered)-set(filtered_utr))

            result[gp_key] = {
                'allele_ids': not_filtered,
                'excluded_allele_ids': {
                    'gene': gp_filtered_gene,
                    'intronic': gp_filtered_intronic,
                    'frequency': gp_filtered_frequency,
                    'utr': filtered_utr,
                }
            }

        return result
