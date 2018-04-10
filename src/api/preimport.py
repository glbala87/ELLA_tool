from collections import OrderedDict
from sqlalchemy import tuple_

from vardb.datamodel import gene

TRANSCRIPT_COLUMNS = OrderedDict()
TRANSCRIPT_COLUMNS["#chromosome"] = lambda t: t.chromosome
TRANSCRIPT_COLUMNS["txStart"] = lambda t: str(t.tx_start)
TRANSCRIPT_COLUMNS["txEnd"] = lambda t: str(t.tx_end)
TRANSCRIPT_COLUMNS["refseq"] = lambda t: t.transcript_name
TRANSCRIPT_COLUMNS["score"] = lambda t: "0"
TRANSCRIPT_COLUMNS["strand"] = lambda t: t.strand
TRANSCRIPT_COLUMNS["geneSymbol"] = lambda t: t.gene.hgnc_symbol
TRANSCRIPT_COLUMNS["HGNC"] = lambda t: str(t.gene.hgnc_id)
TRANSCRIPT_COLUMNS["geneAlias"] = lambda t: ""
TRANSCRIPT_COLUMNS["eGeneID"] = lambda t: t.gene.ensembl_gene_id
TRANSCRIPT_COLUMNS["eTranscriptID"] = lambda t: t.corresponding_ensembl
TRANSCRIPT_COLUMNS["cdsStart"] = lambda t: str(t.cds_start)
TRANSCRIPT_COLUMNS["cdsEnd"] = lambda t: str(t.cds_end)
TRANSCRIPT_COLUMNS["exonsStarts"] = lambda t: ",".join(
    str(es) for es in t.exon_starts)
TRANSCRIPT_COLUMNS["exonEnds"] = lambda t: ",".join(
    str(ee) for ee in t.exon_ends)


PHENOTYPES_COLUMNS = OrderedDict()
PHENOTYPES_COLUMNS["#gene symbol"] = lambda p: p.gene.hgnc_symbol
PHENOTYPES_COLUMNS["HGNC"] = lambda p: str(p.gene.hgnc_id)
PHENOTYPES_COLUMNS["phenotype"] = lambda p: p.description
PHENOTYPES_COLUMNS["inheritance"] = lambda p: p.inheritance
PHENOTYPES_COLUMNS["omim_number"] = lambda p: str(p.omim_id)
PHENOTYPES_COLUMNS["pmid"] = lambda p: str(
    p.pmid) if p.pmid is not None else ""
PHENOTYPES_COLUMNS["inheritance info"] = lambda p: p.inheritance_info
PHENOTYPES_COLUMNS["comment"] = lambda p: p.comment


def _get_phenotype_data(genepanel):
    phenotypes_data = "#\n"+"\t".join(PHENOTYPES_COLUMNS.keys())

    for p in genepanel.phenotypes:
        row = [v(p) for v in PHENOTYPES_COLUMNS.values()]
        phenotypes_data += "\n"+"\t".join(row)
    return phenotypes_data


def _get_transcript_data(genepanel):

    transcript_data = "#\n"+"\t".join(TRANSCRIPT_COLUMNS.keys())

    for t in genepanel.transcripts:
        row = [v(t) for v in TRANSCRIPT_COLUMNS.values()]
        transcript_data += "\n"+"\t".join(row)
    return transcript_data


SLOP_COLUMNS = OrderedDict()
SLOP_COLUMNS["#chromosome"] = lambda t, *args: t.chromosome
SLOP_COLUMNS["start"] = lambda t, start, end, slop, *args: str(start-slop)
SLOP_COLUMNS["end"] = lambda t, start, end, slop, *args: str(end+slop)
SLOP_COLUMNS["exon"] = lambda t, start, end, slop, exon_no: "%s__%s__exon%d" % (
    t.gene.hgnc_symbol, t.transcript_name, exon_no)
SLOP_COLUMNS["someValue"] = lambda t, *args: "0"
SLOP_COLUMNS["strand"] = lambda t, *args: t.strand


def chromsome_sort(t):
    try:
        return int(t.chromosome)
    except ValueError:
        if t.chromosome == "X":
            return 23
        elif t.chromsome == "Y":
            return 24
        elif t.chromosome == "MT":
            return 25


def _get_slop(genepanel, slop):
    slop_data = "\t".join(SLOP_COLUMNS.keys())
    # slop_data = ""
    starts = []
    ends = []
    names = []

    # for t in sorted(genepanel.transcripts, key=lambda t: (chromsome_sort(t), t.tx_start)):
    for t in genepanel.transcripts:
        # SLOP is created from cds start and cds end for the first and last exon, respectively
        ranges = []
        strand = t.strand
        num_exons = len(t.exon_starts)
        for exon_no, (es, ee) in enumerate(zip(t.exon_starts, t.exon_ends)):
            end = False
            if ee < t.cds_start:
                continue
            elif es < t.cds_start:
                es = t.cds_start

            if ee > t.cds_end:
                ee = t.cds_end
                end = True

            if strand == "-":
                ranges.append((es, ee, num_exons-exon_no))
            else:
                ranges.append((es, ee, exon_no+1))
            if end:
                break
        for (es, ee, exon_no) in ranges:
            row = [v(t, es, ee, slop, exon_no) for v in SLOP_COLUMNS.values()]
            slop_data += "\n" + "\t".join(row)
            starts.append(int(row[1]))
            ends.append(int(row[2]))
            names.append(row[3])
    # with open('/ella/src/vardb/testdata/clinicalGenePanels/Ciliopati_v05/Ciliopati_v05.codingExons.bed', 'r') as ref:
    #     ref_starts = []
    #     ref_ends = []
    #     ref_names = []
    #     ref_lines = []
    #     for l in ref:
    #         if l.startswith('#'):
    #             continue
    #         ref_lines.append(l.strip())
    #         l = l.split('\t')
    #         ref_starts.append(int(l[1]))
    #         ref_ends.append(int(l[2]))
    #         ref_names.append(l[3])

    # lines = [l for l in slop_data.split('\n') if not l.startswith('#')]
    # print set(lines) == set(ref_lines)

    # print set(starts) == set(ref_starts)
    # print set(ends) == set(ref_ends)
    # print set(names) == set(ref_names)

    # # print slop_data
    # # print len(slop_data.split('\n'))
    # exit()
    return slop_data


def preimport(session, sample_id, genepanel_name, genepanel_version):
    genepanel = session.query(gene.Genepanel).filter(
        tuple_(gene.Genepanel.name, gene.Genepanel.version) == (
            genepanel_name, genepanel_version)
    ).one()

    metadata = dict()

    files = dict()
    basename = "%s_%s" % (genepanel_name, genepanel_version)

    files["TRANSCRIPTS"] = (basename+"_transcripts.csv",
                            _get_transcript_data(genepanel))
    files["PHENOTYPES"] = (basename+"_phenotypes.csv",
                           _get_phenotype_data(genepanel))
    files["SLOP2"] = (basename+"_slop2.bed", _get_slop(genepanel, 2))
    files["SLOP20"] = (basename+"slop20.bed", _get_slop(genepanel, 20))
    files["SLOP20000"] = (basename+"slop20.bed", _get_slop(genepanel, 20000))

    files["REPORT_CONFIG"] = (basename+"_report_config.txt", "[DEFAULT]\ntitle={gp_name}\nversion={gp_version}".format(
        gp_name=genepanel_name, gp_version=genepanel_version))

    fields = dict()
    fields['targets'] = ['test_target']
    fields['ANALYSIS_NAME'] = "%s.%s_%s" % (
        sample_id, genepanel_name, genepanel_version)

    return files, fields


if __name__ == "__main__":
    from vardb.util.db import DB
    db = DB()
    db.connect()
    session = db.session
    print dir(session)
    exit()
    genepanel_name = "HBOC"
    genepanel_version = "v01"
    sample_id = 'Diag-excap1-NA12878'

    files, fields = preimport(
        session, sample_id, genepanel_name, genepanel_version)

    analysis_name = "FOOBAR.%s_%s" % (genepanel_name, genepanel_version)
    from api.util.genepanel_to_bed import genepanel_to_bed
    regions = genepanel_to_bed(session, genepanel_name, genepanel_version)
    files["regions"] = ('regions.bed', regions)
    fields["ANALYSIS_NAME"] = analysis_name
    fields["sample_id"] = 'Diag-excap1-NA12878'

    import urllib2
    import os
    import binascii

    def encode_multipart_formdata(fields, files):
        LIMIT = "-"*10 + binascii.hexlify(os.urandom(10))
        CRLF = '\r\n'
        L = []
        for (key, value) in fields.iteritems():
            L.append('--' + LIMIT)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            if isinstance(value, basestring):
                if not value.startswith('"'):
                    value = '"'+value
                if not value.endswith('"'):
                    value = value + '"'
            value = str(value)
            L.append(value)
        for (key, (filename, value)) in files.iteritems():
            L.append('--' + LIMIT)
            L.append(
                'Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: application/octet-stream')
            L.append('')
            L.append(value)
        L.append('--' + LIMIT + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % LIMIT
        return content_type, body

    content_type, body = encode_multipart_formdata(fields, files)
    print body

    r = urllib2.Request("http://172.17.0.1:6000/api/v1/samples/annotate",
                        data=body, headers={"Content-type": content_type})
    urllib2.urlopen(r)
