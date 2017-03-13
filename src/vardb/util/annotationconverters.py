import re
import json
import base64
from collections import defaultdict

import logging

log = logging.getLogger(__name__)


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
CSQ_INTRON_CHECK_REGEX = re.compile(r'.*c\.[0-9]+?(?P<plus_minus>[\-\+])(?P<distance>[0-9]+)')


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
        # Filter out non-transcripts
        if data.get('Feature_type') != 'Transcript':
            continue

        transcript_data = {k[1]: data[k[0]] for k in CSQ_FIELDS if k[0] in data}

        # Only keep dbSNP data (e.g. rs123456789)
        if 'dbsnp' in transcript_data:
            transcript_data['dbsnp'] = [t for t in transcript_data['dbsnp'] if t.startswith('rs')]

        # Convert 'is_canonical' to bool
        transcript_data['is_canonical'] = transcript_data.get('is_canonical') == 'YES'

        # Add custom types
        if 'HGVSc' in transcript_data:
            # Split away transcript part
            transcript_data['HGVSc_short'] = transcript_data['HGVSc'].split(':', 1)[1]

            exon_distance = _get_exon_distance(transcript_data)
            if exon_distance is not None:
                transcript_data['exon_distance'] = exon_distance

        if 'HGVSp' in transcript_data:
            transcript_data['HGVSp_short'] = transcript_data['HGVSp'].split(':', 1)[1]

        transcript_data['in_last_exon'] = 'yes' if _get_is_last_exon(transcript_data) else 'no'
        transcripts.append(transcript_data)

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


def exac_frequencies(annotation):
    """
    Manually calculate frequencies from raw ExAC data.

    :param: annotation: a dict with key 'EXAC'
    :returns: dict with key 'ExAC'
    """

    if 'EXAC' not in annotation:
        return {}
    frequencies = defaultdict(dict)

    freq = {}
    count = {}
    num = {}
    hom = {}
    het = {}
    for key, value in annotation['EXAC'].iteritems():
        # Be careful if rearranging!
        if key == 'AC_Adj':
            assert len(value) == 1
            count['G'] = value[0]
        elif key == 'AC_Het':
            assert len(value) == 1
            het['G'] = value[0]
        elif key == 'AC_Hom':
            assert len(value) == 1
            hom['G'] = value[0]
        elif key == 'AN_Adj':
            num['G'] = value
        elif key.startswith('AC_'):
            pop = key.split('AC_')[1]
            assert len(value) == 1
            count[pop] = value[0]
        elif key.startswith('AN_'):
            pop = key.split('AN_')[1]
            num[pop] = value
        elif key.startswith('Hom_'):
            pop = key.split('Hom_')[1]
            # TODO: Remove me when we got our annotation under control...
            if isinstance(value, list):
                hom[pop] = value[0]
            else:
                hom[pop] = value
        elif key.startswith('Het_'):
            pop = key.split('Het_')[1]
            if isinstance(value, list):
                het[pop] = value[0]
            else:
                het[pop] = value

    for key in count:
        if key in num and num[key]:
            freq[key] = float(count[key]) / num[key]

    if freq:
        frequencies['ExAC'].update({'freq': freq})
    if hom:
        frequencies['ExAC'].update({'hom': hom})
    if het:
        frequencies['ExAC'].update({'het': het})
    if num:
        frequencies['ExAC'].update({'num': num})
    if count:
        frequencies['ExAC'].update({'count': count})

    return dict(frequencies)


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


def indb_frequencies(annotation):
    if 'inDB' not in annotation:
        return {}

    frequencies = dict(freq=dict(), count=dict(), indications=dict())
    if "AF_OUSWES" in annotation["inDB"]:
        frequencies["freq"]["AF"] = annotation["inDB"]["AF_OUSWES"]
    elif 'alleleFreq' in annotation["inDB"]:
        frequencies["freq"]["AF"] = annotation["inDB"]["alleleFreq"]
    else:
        log.warning("inDB key present, bug missing supported frequency key")

    if "AC_OUSWES" in annotation["inDB"]:
        frequencies["count"]["AF"] = annotation["inDB"]["AC_OUSWES"]
    elif 'noMutInd' in annotation['inDB']:
        frequencies["count"]["AF"] = annotation["inDB"]["noMutInd"]
    else:
        log.warning("inDB key present, bug missing supported allele count key")

    if "indications_OUSWES" in annotation["inDB"]:
        frequencies["indications"] = annotation['inDB']['indications_OUSWES']
    elif 'indications' in annotation['inDB']:
        frequencies["indications"] = annotation['inDB']['indications']
    else:
        log.warning("inDB key present, bug missing supported indications key")

    return {'inDB': frequencies}


class ConvertReferences(object):

    REFTAG = {
        "APR": "Additional phenotype",
        "FCR": "Functional characterisation",
        "MCR": "Molecular characterisation",
        "SAR": "Additional report",
    }

    def _csq_pubmeds(self, annotation):
        if 'CSQ' not in annotation:
            return dict()
        # Get first elem which has PUBMED ids (it's the same in all elements)
        pubmed_data = next((d['PUBMED'] for d in annotation['CSQ'] if 'PUBMED' in d), list())
        pubmed_data = dict(zip(pubmed_data, [""]*len(pubmed_data)))  # Return as dict (empty values)
        return pubmed_data

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

        for er in annotation["HGMD"].get("extrarefs",[]):
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
        csq_pubmeds = self._ensure_int_pmids(self._csq_pubmeds(annotation))
        hgmd_pubmeds = self._ensure_int_pmids(self._hgmd_pubmeds(annotation))
        clinvar_pubmeds = self._ensure_int_pmids(self._clinvar_pubmeds(annotation))

        # Merge references and restructure to list
        all_pubmeds = csq_pubmeds.keys()+hgmd_pubmeds.keys()+clinvar_pubmeds.keys()
        references = list()
        for pmid in sorted(set(all_pubmeds), key=all_pubmeds.count, reverse=True):
            sources = []
            sourceInfo = dict()
            if pmid in csq_pubmeds:
                sources.append("VEP")
                if csq_pubmeds[pmid] != "":
                    sourceInfo["VEP"] = csq_pubmeds[pmid]
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
