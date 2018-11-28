from vardb.datamodel import annotation
import operator
from sqlalchemy import and_, or_, literal_column, func

OPERATORS = {
    '==': operator.eq,
    '>=': operator.ge,
    '<=': operator.le,
    '>': operator.gt,
    '<': operator.lt
}

HGMD_TAGS = set([None, 'FP', 'DM', 'DFP', 'R', 'DP', 'DM?'])

class ExternalFilter(object):

    def __init__(self, session, config):
        self.session = session
        self.config = config

    def _build_clinvar_filters(self, clinsig_counts, combinations):
        def get_filter_count(v):
            if isinstance(v, basestring):
                assert v in ['benign', 'pathogenic', 'uncertain']
                return getattr(clinsig_counts.c, v)
            else:
                return v

        filters = []
        for c in combinations:
            clinsig, op, count = c[0], OPERATORS[c[1]], get_filter_count(c[2])
            filters.append(op(getattr(clinsig_counts.c, clinsig), count))
        return filters

    def _filter_clinvar(self, allele_ids, clinvar_config):
        # Use this to evaluate the number of stars
        star_op, num_stars = clinvar_config.get('num_stars', ('>=', 0))
        star_op = OPERATORS[star_op]

        filter_signifiance_descr = [k for k,v in self.config['annotation']['clinvar']['clinical_significance_status'].items() if star_op(v,num_stars)]

        combinations = clinvar_config.get('combinations', [])

        # Expand clinvar submissions
        expanded_clinvar = self.session.query(
            annotation.Annotation.allele_id,
            literal_column("jsonb_array_elements(annotations->'external'->'CLINVAR'->'items')").label('entry'),
        ).filter(
            annotation.Annotation.allele_id.in_(allele_ids),
            annotation.Annotation.date_superceeded.is_(None),
        ).subquery()

        # Extract clinical significance for all SCVs
        clinvar_clinsigs = self.session.query(
            expanded_clinvar.c.allele_id,
            expanded_clinvar.c.entry.op('->>')('rcv').label('scv'),
            expanded_clinvar.c.entry.op('->>')('clinical_significance_descr').label('clinsig')
        ).filter(
            expanded_clinvar.c.entry.op('->>')('rcv').op('ILIKE')('SCV%')
        ).subquery()

        def count_matches(pattern):
            return func.count(clinvar_clinsigs.c.clinsig).filter(clinvar_clinsigs.c.clinsig.op('ILIKE')(pattern))

        # Count the number of Pathogenic/Likely pathogenic, Uncertain significance, and Benign/Likely benign
        clinsig_counts = self.session.query(
            clinvar_clinsigs.c.allele_id,
            count_matches('%pathogenic%').label('pathogenic'),
            count_matches('%uncertain%').label('uncertain'),
            count_matches('%benign%').label('benign'),
            func.count(clinvar_clinsigs.c.clinsig).label('total')
        ).group_by(
            clinvar_clinsigs.c.allele_id
        ).order_by(clinvar_clinsigs.c.allele_id).subquery()

        filters = self._build_clinvar_filters(clinsig_counts, combinations)

        # Extract allele ids that matches the config rules
        filtered_allele_ids = self.session.query(
            clinsig_counts.c.allele_id,
        ).join(
            annotation.Annotation,
            annotation.Annotation.allele_id == clinsig_counts.c.allele_id
        ).filter(
            and_(*filters),
            annotation.Annotation.date_superceeded.is_(None),
            annotation.Annotation.annotations.op('->')('external').op('->')('CLINVAR').op('->>')('variant_description').in_(filter_signifiance_descr)
        )

        return set([a[0] for a in filtered_allele_ids])

    def _filter_hgmd(self, allele_ids, hgmd_config):

        hgmd_tags = hgmd_config['tags']
        assert not set(hgmd_tags) - HGMD_TAGS, "Invalid tag(s) to filter on in {}. Available tags are {}.".format(hgmd_tags, HGMD_TAGS)

        # Need to separate check for specific tag and check for no HGMD data (tag is None)
        filters = []
        if None in hgmd_tags:
            hgmd_tags.pop(hgmd_tags.index(None))
            filters.append(annotation.Annotation.annotations.op('->')('external').op('->')('HGMD').op('->>')('tag').is_(None))

        if hgmd_tags:
            filters.append(annotation.Annotation.annotations.op('->')('external').op('->')('HGMD').op('->>')('tag').in_(hgmd_tags))

        filtered_allele_ids = self.session.query(
            annotation.Annotation.allele_id,
        ).filter(
            annotation.Annotation.date_superceeded.is_(None),
            annotation.Annotation.allele_id.in_(allele_ids),
            or_(*filters)
        )

        return set([a[0] for a in filtered_allele_ids])


    def filter_alleles(self, gp_allele_ids, filter_config):
        """
        Filter alleles on external annotations. Supported external databases are clinvar and hgmd.
        Filters only alleles which satisify *both* clinvar and hgmd configurations. If only one of clinvar or
        hgmd is specified, filters on this alone.

        filter_config is specified like
        {
            "clinvar": {
                "combinations": [
                    ["benign", ">", 5], # More than 5 benign submissions
                    ["pathogenic", "==", 0], # No pathogenic submissions
                    ["benign", ">", "uncertain"] # More benign than pathogenic submissions
                ],
                "num_stars": [">=", 2] # Only include variants with 2 or more stars
            },
            "hgmd": {
                "tags": [None], # Not in HGMD
            }
        }

        """
        result = dict()
        for gp_key, allele_ids in gp_allele_ids.iteritems():
            if not allele_ids:
                result[gp_key] = set()

            clinvar_config = filter_config.get('clinvar')
            if clinvar_config:
                clinvar_filtered_allele_ids = self._filter_clinvar(allele_ids, clinvar_config)
            else:
                clinvar_filtered_allele_ids = None

            hgmd_config = filter_config.get('hgmd')
            if hgmd_config:
                hgmd_filtered_allele_ids = self._filter_hgmd(allele_ids, hgmd_config)
            else:
                hgmd_filtered_allele_ids = None

            # Union hgmd filtered and clinvar filtered if both have been run, otherwise return the result of the run one
            if clinvar_filtered_allele_ids is not None and hgmd_filtered_allele_ids is not None:
                result[gp_key] = clinvar_filtered_allele_ids & hgmd_filtered_allele_ids
            elif clinvar_filtered_allele_ids is not None:
                result[gp_key] = clinvar_filtered_allele_ids
            elif hgmd_filtered_allele_ids is not None:
                result[gp_key] = hgmd_filtered_allele_ids
            else:
                result[gp_key] = set()

        return result
