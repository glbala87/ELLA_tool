import re
import json
import base64
from collections import defaultdict

import logging

log = logging.getLogger(__name__)

# the annotation key is found in the VCF
# the result key is put in our annotation database
EXAC_ANNOTATION_KEY = 'EXAC'
EXAC_RESULT_KEY = 'ExAC'

GNOMAD_EXOMES_ANNOTATION_KEY = 'GNOMAD_EXOMES'
GNOMAD_EXOMES_RESULT_KEY = 'GNOMAD_EXOMES'

GNOMAD_GENOMES_ANNOTATION_KEY = 'GNOMAD_GENOMES'
GNOMAD_GENOMES_RESULT_KEY = 'GNOMAD_GENOMES'

INDB_ANNOTATION_KEY = 'inDB'
INDB_RESULT_KEY = 'inDB'

SPLICE_FIELDS = [
    ('Effect', 'effect'),
    ('Transcript', 'transcript'),
    ('MaxEntScan-mut', 'maxentscan_mut'),
    ('MaxEntScan-wild', 'maxentscan_wild'),
    ('MaxEntScan-closest', 'maxentscan_closest'),  # relevant for 'de novo'
    ('dist', 'dist')  # relevant for 'de novo'
]


def convert_splice(annotation):
    if 'splice' not in annotation:
        return list()

    transcripts = list()

    for data in annotation['splice']:
        if 'Transcript' not in data:
            continue

        splice_data = {k[1]: data[k[0]] for k in SPLICE_FIELDS if k[0] in data}

        transcript = next((t for t in transcripts if t['transcript'] == splice_data['transcript']), None)

        if transcript:
            transcript['splice'].append(splice_data)
        else:
            transcripts.append({
                'transcript': splice_data['transcript'],
                'splice': [splice_data]
            })

    return transcripts


CSQ_FIELDS = [
    # (source, dest) key names
    ('Consequence', 'consequences'),
    ('HGNC_ID', 'hgnc_id'),
    ('SYMBOL', 'symbol'),
    ('HGVSc', 'HGVSc'),
    ('HGVSp', 'HGVSp'),
    ('STRAND', 'strand'),
    ('Amino_acids', 'amino_acids'),
    ('Existing_variation', 'dbsnp'),
    ('EXON', 'exon'),
    ('INTRON', 'intron'),
    ('Codons', 'codons'),
    ('Feature', 'transcript'),
    ('CANONICAL', 'is_canonical')

]

# Matches NM_007294.3:c.4535-213G>T  (gives ['-', '213'])
# but not NM_007294.3:c.4535G>T
CSQ_INTRON_CHECK_REGEX = re.compile(r'[cn]\.[\-\*]?[0-9]+?(?P<plus_minus>[\-\+])(?P<distance>[0-9]+)')


def _map_hgnc_id(transcripts):
    symbol_hgnc_id = dict()
    for t in transcripts:
        if t.get('hgnc_id') and isinstance(t.get('hgnc_id'), int):
            if t['symbol'] in symbol_hgnc_id:
                assert symbol_hgnc_id[t['symbol']] == t['hgnc_id'], 'Got different HGNC ({} vs {}) id for same gene symbol ({})'.format(t['hgnc_id'], symbol_hgnc_id[t['symbol']], t['symbol'])
            symbol_hgnc_id[t['symbol']] = t['hgnc_id']
    return symbol_hgnc_id


def convert_csq(annotation):
    def _get_is_last_exon(transcript_data):
        exon = transcript_data.get('exon')
        if exon:
            parts = exon.split('/')
            return parts[0] == parts[1]
        return False

    def _get_exon_distance(transcript_data):
        """
        Gets distance from exon according to HGVSc position (for intron variants).
        """
        hgvsc = transcript_data.get('HGVSc')
        match = re.match(CSQ_INTRON_CHECK_REGEX, hgvsc)
        if match:
            match_data = match.groupdict()

            # Regex should guarantee int conversion is possible
            plus_minus, distance = match_data['plus_minus'], int(match_data['distance'])
            if plus_minus == '+':
                assert distance >= 0
                return distance
            elif plus_minus == '-':
                assert distance > 0
                return -distance

        return None

    if 'CSQ' not in annotation:
        return list()

    transcripts = list()
    # Invert CSQ data to map to transcripts
    for data in annotation['CSQ']:
        # Filter out non-transcripts,
        # and only include normal RefSeq or Ensembl transcripts
        if data.get('Feature_type') != 'Transcript' or \
           not any(data.get('Feature', '').startswith(t) for t in ['NM_', 'ENST']):
            continue

        transcript_data = {k[1]: data[k[0]] for k in CSQ_FIELDS if k[0] in data}

        if 'hgnc_id' in transcript_data:
            transcript_data['hgnc_id'] = int(transcript_data['hgnc_id'])

        # Only keep dbSNP data (e.g. rs123456789)
        if 'dbsnp' in transcript_data:
            transcript_data['dbsnp'] = [t for t in transcript_data['dbsnp'] if t.startswith('rs')]

        # Convert 'is_canonical' to bool
        transcript_data['is_canonical'] = transcript_data.get('is_canonical') == 'YES'

        # Add custom types
        if 'HGVSc' in transcript_data:

            transcript_name, hgvsc = transcript_data['HGVSc'].split(':', 1)
            transcript_data['HGVSc'] = hgvsc  # Remove transcript part

            # Split away transcript part and remove long (>10 nt) insertions/deletions/duplications
            def repl_len(m):
                return "("+str(len(m.group()))+")"

            s = re.sub('(?<=ins)([ACGT]{10,})', repl_len, hgvsc)
            insertion = re.search('(?<=ins)([ACGT]{10,})', hgvsc)
            if insertion is not None:
                transcript_data["HGVSc_insertion"] = insertion.group()
            s = re.sub('(?<=[del|dup])[ACGT]{10,}', '', s)
            transcript_data['HGVSc_short'] = s

            exon_distance = _get_exon_distance(transcript_data)
            if exon_distance is not None:
                transcript_data['exon_distance'] = exon_distance

        if 'HGVSp' in transcript_data:  # Remove transcript part
            transcript_data['protein'], transcript_data['HGVSp'] = transcript_data['HGVSp'].split(':', 1)

        transcript_data['in_last_exon'] = 'yes' if _get_is_last_exon(transcript_data) else 'no'
        transcripts.append(transcript_data)

    # Hack: Since hgnc_id is not provided by VEP for Refseq,
    # we steal it from matching Ensembl transcript (by gene symbol)
    # Tested on 100k exome annotated variants, all RefSeq had corresponding match in Ensembl
    symbol_hgnc_id = _map_hgnc_id(transcripts)
    for t in transcripts:
        if not t.get('hgnc_id') and t.get('symbol') and t['symbol'] in symbol_hgnc_id:
            t['hgnc_id'] = symbol_hgnc_id[t['symbol']]

    return transcripts


HGMD_FIELDS = [
    'acc_num',
    'codon',
    'disease',
    'tag',
]


def convert_hgmd(annotation):
    if 'HGMD' not in annotation:
        return dict()

    data = {k: annotation['HGMD'][k] for k in HGMD_FIELDS if k in annotation['HGMD']}
    return {'HGMD': data}


CLINVAR_RCV_FIELDS = [
    'traitnames',
    'clinical_significance_descr',
    #'clinical_significance_status',
    'variant_id',
    'submitter',
    'last_evaluated'
]

CLINVAR_FIELDS = [
    'variant_description',
    'variant_id'
]


def convert_clinvar(annotation):
    if 'CLINVARJSON' not in annotation:
        return dict()

    clinvarjson = json.loads(base64.b16decode(annotation['CLINVARJSON']))

    if any(k not in clinvarjson for k in CLINVAR_FIELDS):
        return dict()

    data = dict(items=[])
    data.update({k: clinvarjson[k] for k in CLINVAR_FIELDS})
    for rcv, val in clinvarjson["rcvs"].items():
        item = {k: ", ".join(val[k]) for k in CLINVAR_RCV_FIELDS}
        item["rcv"] = rcv
        data["items"].append(item)

    return {'CLINVAR': data}


def extract_annotation_data(annotation, annotation_key, result_key):
    frequencies = defaultdict(dict)

    # TODO: Remove when annotation isn't so messed up...
    def extract_int_list(value):
        if isinstance(value, list):
            assert len(value) == 1
            value = value[0]
        value = int(value)
        return value

    freq = {}
    count = {}
    num = {}
    hom = {}
    hemi = {}
    filter_status = {}
    indications = {}
    for key, value in annotation[annotation_key].iteritems():
        if key == 'AS_FilterStatus':  # gnomAD specific
            assert len(value) == 1
            filter_status = {
                'G': value[0].split('|')
            }
        elif key.startswith('filter_'):
            pop = key.split('filter_')[1]
            filter_status[pop] = re.split(',|\|', value)
        # Be careful if rearranging!
        elif key == 'AC':
            assert len(value) == 1
            count['G'] = value[0]
        elif key == 'AC_Hom':
            assert len(value) == 1
            hom['G'] = value[0]
        elif key == 'AN':
            num['G'] = value
        elif key.startswith('AC_'):
            pop = key.split('AC_')[1]
            assert len(value) == 1
            count[pop] = value[0]
        elif key.startswith('AN_'):
            pop = key.split('AN_')[1]
            num[pop] = extract_int_list(value)
        elif key.startswith('Hom_'):
            pop = key.split('Hom_')[1]
            hom[pop] = extract_int_list(value)
        elif key.startswith('Hemi_'):
            pop = key.split('Hemi_')[1]
            hemi[pop] = extract_int_list(value)
        elif key.startswith('indications_'):
            pop = key.split('indications_')[1]
            indications[pop] = {f.split(':', 1)[0]: f.split(':', 1)[1] for f in value.split(',')}

    for key in count:
        if key in num and num[key]:
            freq[key] = float(count[key]) / num[key]

    # ExAC override. ExAC naming is very misleading!
    # ExAC should use Adj, NOT the default AC and AN!
    if result_key == EXAC_RESULT_KEY:
        for item in [count, num, freq]:
            if 'Adj' in item:
                item['G'] = item['Adj']
                del item['Adj']

    if freq:
        frequencies[result_key].update({'freq': freq})
    if hom:
        frequencies[result_key].update({'hom': hom})
    if hemi:
        frequencies[result_key].update({'hemi': hemi})
    if num:
        frequencies[result_key].update({'num': num})
    if count:
        frequencies[result_key].update({'count': count})
    if filter_status:
        frequencies[result_key].update({'filter': filter_status})
    if indications:
        frequencies[result_key].update({'indications': indications})

    return dict(frequencies)


def exac_frequencies(annotation):
    """
    Manually calculate frequencies from raw ExAC data.

    :param: annotation: a dict with key 'EXAC'
    :returns: dict with key 'ExAC'
    """

    if EXAC_ANNOTATION_KEY not in annotation:
        return {}
    else:
        return extract_annotation_data(
            annotation, EXAC_ANNOTATION_KEY, EXAC_RESULT_KEY
        )


def gnomad_exomes_frequencies(annotation):
    """
    Manually calculate frequencies from raw GNOMAD Exomoes data.

    :param: annotation: a dict with key 'GNOMAD_EXOMES'
    :returns: dict with key 'GNOMAD_EXOMES'
    """

    if GNOMAD_EXOMES_ANNOTATION_KEY not in annotation:
        return {}
    else:
        return extract_annotation_data(
            annotation, GNOMAD_EXOMES_ANNOTATION_KEY, GNOMAD_EXOMES_RESULT_KEY
        )


def gnomad_genomes_frequencies(annotation):
    """
    Manually calculate frequencies from raw Gnomad Genomes data.

    :param: annotation: a dict with key 'GNOMAD_GENOMES'
    :returns: dict with key 'GNOMAD_GENOMES'
    """

    if GNOMAD_GENOMES_ANNOTATION_KEY not in annotation:
        return {}
    else:
        return extract_annotation_data(
            annotation, GNOMAD_GENOMES_ANNOTATION_KEY, GNOMAD_GENOMES_RESULT_KEY
        )


def indb_frequencies(annotation):
    """
    Manually calculate frequencies from raw Gnomad Genomes data.

    :param: annotation: a dict with key 'GNOMAD_GENOMES'
    :returns: dict with key 'GNOMAD_GENOMES'
    """
    if INDB_ANNOTATION_KEY not in annotation:
        return {}
    else:
        return extract_annotation_data(
            annotation, INDB_ANNOTATION_KEY, INDB_RESULT_KEY
        )


def csq_frequencies(annotation):
    if 'CSQ' not in annotation:
        return {}

    # Get first elem which has frequency data (it's the same in all elements)
    frequencies = dict()
    freq_data = next((d for d in annotation['CSQ'] if any('MAF' in k for k in d)), None)
    if freq_data:
        # Check whether the allele provided for the frequency is the same as the one we have in our allele.
        # VEP gives minor allele for some fields, which can be the reference instead of the allele
        processed = {
            k.replace('_MAF', '').replace('MAF', ''): v[freq_data['Allele']]
            for k, v in freq_data.iteritems()
            if 'MAF' in k and
            freq_data['Allele'] in v
        }
        if processed:
            # ESP6500 freqs
            esp6500_freq = dict()
            for f in ['AA', 'EA']:
                if f in processed:
                    esp6500_freq[f] = processed.pop(f)
            if esp6500_freq:
                frequencies['esp6500'] = {'freq': esp6500_freq}

            if processed:
                frequencies['1000g'] = {'freq': processed}

    return dict(frequencies)


class ConvertReferences(object):

    REFTAG = {
        "APR": "Additional phenotype",
        "FCR": "Functional characterisation",
        "MCR": "Molecular characterisation",
        "SAR": "Additional report",
    }

    def _hgmd_pubmeds(self, annotation):
        if 'HGMD' not in annotation:
            return dict()
        total = dict()

        if 'pmid' in annotation['HGMD']:
            pmid = annotation['HGMD']['pmid']
            reftag = "Primary literature report"
            comments = annotation['HGMD'].get("comments", "No comments")
            comments = "No comments." if comments == "None" else comments
            total[pmid] = [reftag, comments]

        for er in annotation["HGMD"].get("extrarefs", []):
            if "pmid" in er:
                pmid = er['pmid']
                reftag = ConvertReferences.REFTAG.get(er.get("reftag"), "Reftag not specified")
                comments = annotation['HGMD'].get("comments", "No comments.")
                comments = "No comments." if comments == "None" else comments
                total[pmid] = [reftag, comments]

        # Format reftag, comments to string
        for pmid, info in total.items():
            info_string = ". ".join([v.strip().strip('.') for v in info])+"."
            total[pmid] = info_string

        return total

    def _clinvar_pubmeds(self, annotation):
        if 'CLINVARJSON' not in annotation:
            return dict()

        clinvarjson = json.loads(base64.b16decode(annotation['CLINVARJSON']))

        pubmeds = clinvarjson["pubmeds"]
        pubmeds = dict(zip(pubmeds, [""]*len(pubmeds)))  # Return as dict (empty values)

        return pubmeds

    def _ensure_int_pmids(self, pmids):
        # HACK: Convert all ids to int, the annotation is sometimes messed up
        # If it cannot be converted, ignore it...
        assert isinstance(pmids, dict)
        int_pmids = dict()
        for pmid, val in pmids.iteritems():
            try:
                int_pmids[int(pmid)] = val
            except ValueError:
                log.warning("Cannot convert pubmed id from annotation to integer: {}".format(val))

        return int_pmids

    def process(self, annotation):
        hgmd_pubmeds = self._ensure_int_pmids(self._hgmd_pubmeds(annotation))
        clinvar_pubmeds = self._ensure_int_pmids(self._clinvar_pubmeds(annotation))

        # Merge references and restructure to list
        all_pubmeds = hgmd_pubmeds.keys() + clinvar_pubmeds.keys()
        references = list()
        for pmid in sorted(set(all_pubmeds), key=all_pubmeds.count, reverse=True):
            sources = []
            sourceInfo = dict()
            if pmid in hgmd_pubmeds:
                sources.append("HGMD")
                if hgmd_pubmeds[pmid] != "":
                    sourceInfo["HGMD"] = hgmd_pubmeds[pmid]
            if pmid in clinvar_pubmeds:
                sources.append("CLINVAR")
                if clinvar_pubmeds[pmid] != "":
                    sourceInfo["CLINVAR"] = clinvar_pubmeds[pmid]

            references.append({
                'pubmed_id': pmid, 'sources': sources, "source_info": sourceInfo,
            })

        return references
