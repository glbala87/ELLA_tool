import datetime
import os

import hgvs.parser
import hgvs.variantmapper
import hgvs.dataproviders.uta
import hgvs.exceptions
from pygr.seqdb import SequenceFileDB
from vardb.deposit.vcfutil import vcfhelper

import logging
logging.basicConfig(level=logging.INFO)

"""
Convert a tsv file with classification data into a VCF.
The file should/must contain: 
- classification (1-5),
- username of the person that did the classification
- report text (base64 encoded)
- assessment text (base64 encoded)

The script is typically run like:
python src/excel/variant_to_vcf.py --reference gatkBundle_2.5/human_g1k_v37_decoy.fasta PTEN-c.-1026CA.tsv

To make a tsv file from Excel, see 'parse_ekg_variant' script in the ella-amg repo.
"""

VCF_HEADER = """##fileformat=VCFv4.1
##INFO=<ID=CLASS,Number=.,Type=String,Description="Assessment classification">
##INFO=<ID=REPORT_COMMENT,Number=.,Type=String,Description="An comment belong to an assessment report (base64, utf-8)">
##INFO=<ID=ASSESSMENT_COMMENT,Number=.,Type=String,Description="A comment made on classification evaluation (base64, utf-8)">
##INFO=<ID=HGVSC_ORIGIN,Number=.,Type=String,Description="cDNA that was origin for this vcf line. For audit purposes.">
##INFO=<ID=DATE,Number=.,Type=String,Description="Date of classification.">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{name}
"""


class VcfWriter(object):

    VCF_LINE = '{chr}\t{pos}\tHBLANK\t{ref}\t{alt}\t.\t.\t{info};\tGT\t./.\n'

    def __init__(self, path, name):
        self.path = path
        self.name = name
        self.fd = None

    def __enter__(self):
        if not self.fd:
            self.fd = open(self.path, 'w')
        self.write_header()

    def __exit__(self, type, value, traceback):
        if self.fd:
            self.fd.close()

    def write_header(self):
        if not self.fd:
            self.fd = open(self.path, 'a')
        self.fd.write(VCF_HEADER.format(name=self.name))

    def write_data(self, data):
        infos = [
            'HGVSC_ORIGIN={}:{}'.format(data['transcript'], data['hgvsc']),
            'DATE={}'.format(data['date']),
            'CLASS={}'.format(data['classification']),
            'USERNAME={}'.format(data['username']),
            'REPORT_COMMENT={}'.format(data['historic_answer']),
            'ASSESSMENT_COMMENT={}'.format(data['historic_assessments'])
        ]
        data['info'] = ';'.join(infos)
        self.fd.write(VcfWriter.VCF_LINE.format(**data))

    def close(self):
        self.fd.close()


class ReferenceConverter(object):

    REFSEQ_ACCESSION = {
        'hg19': {
            '1': "NC_000001.10",    '2': "NC_000002.11",    '3': "NC_000003.11",
            '4': "NC_000004.11",    '5': "NC_000005.9",    '6': "NC_000006.11",
            '7': "NC_000007.13",    '8': "NC_000008.10",    '9': "NC_000009.11",
            '10': "NC_000010.10",    '11': "NC_000011.9",    '12': "NC_000012.11",
            '13': "NC_000013.10",    '14': "NC_000014.8",    '15': "NC_000015.9",
            '16': "NC_000016.9",    '17': "NC_000017.10",    '18': "NC_000018.9",
            '19': "NC_000019.9",    '20': "NC_000020.10",    '21': "NC_000021.8",
            '22': "NC_000022.10",    'X': "NC_000023.10",    'Y': "NC_000024.9",
        },
        'hg38': {
            '1': "NC_000001.11",    '2': "NC_000002.12",    '3': "NC_000003.12",
            '4': "NC_000004.12",    '5': "NC_000005.10",    '6': "NC_000006.12",
            '7': "NC_000007.14",    '8': "NC_000008.11",    '9': "NC_000009.12",
            '10': "NC_000010.11",    '11': "NC_000011.10",    '12': "NC_000012.12",
            '13': "NC_000013.11",    '14': "NC_000014.9",    '15': "NC_000015.10",
            '16': "NC_000016.10",    '17': "NC_000017.11",    '18': "NC_000018.10",
            '19': "NC_000019.10",    '20': "NC_000020.11",    '21': "NC_000021.9",
            '22': "NC_000022.11",    'X': "NC_000023.101",    'Y': "NC_000024.10",
        }
    }

    def __init__(self, fasta):
        self.hgvsparser = hgvs.parser.Parser()
        self.variantmapper = hgvs.variantmapper.EasyVariantMapper(
            hgvs.dataproviders.uta.connect(),
            primary_assembly=u'GRCh37',
        )
        self.seqdb = SequenceFileDB(fasta)

    def _convert_cdna(self, cdna):
        var_c = self.hgvsparser.parse_hgvs_variant(cdna)
        var_g = self.variantmapper.c_to_g(var_c)
        return var_g

    def _get_chr(self, accession):
        """
        Fetches chromosome from reference accession.
        """
        return next(k for k, v in ReferenceConverter.REFSEQ_ACCESSION['hg19'].iteritems() if v == accession)


class ExcelExporter(object):

    TSV_FIELDS = [
        'transcript',
        'hgvsc',
        'classification',
        'username',
        'date',
        'historic_assessments',
        'historic_answer'
    ]

    def __init__(self, fasta):
        self.converter = ReferenceConverter(fasta)

    def parse_exported(self, variants, output):

        vcf_writer = VcfWriter(output, 'Exported_{}'.format(datetime.datetime.today().strftime('%Y-%m-%d')))
        allele_creator = vcfhelper.VCFAlleleCreator(self.converter.seqdb)

        with vcf_writer:
            number_of_skips = 0
            for idx, line in enumerate(variants):
                if line.startswith('#'):
                    number_of_skips += 1
                    continue
                fields = dict(zip(ExcelExporter.TSV_FIELDS, [c.strip() for c in line.split('\t')]))
                transcript_hgvsc = "{}:{}".format(fields['transcript'], fields['hgvsc'])
                logging.info("Processing {} ({} of {})".format(transcript_hgvsc, idx+1-number_of_skips, len(variants)-number_of_skips))
                try:
                    try:
                        var_c = self.converter._convert_cdna(transcript_hgvsc)
                    except hgvs.exceptions.HGVSError:
                        logging.exception("Error while parsing fields {}, it will not be included.".format(transcript_hgvsc))
                        continue
                    except AttributeError:
                        logging.exception("Internal error while parsing fields {}, it will not be included.".format(transcript_hgvsc))
                        continue

                    if var_c.posedit.pos.uncertain:
                        logging.warning('Position uncertain for fields {}, it will not be included!'.format(transcript_hgvsc))
                        continue

                    chrom = self.converter._get_chr(var_c.ac)
                    ref = var_c.posedit.edit.ref
                    if hasattr(var_c.posedit.edit, 'alt'):
                        alt = var_c.posedit.edit.alt
                    else:
                        alt = None
                    start = var_c.posedit.pos.start.base
                    end = var_c.posedit.pos.end.base

                    vcf_data = dict(fields)
                    vcf_data['chr'] = chrom

                    # dup:
                    if not hasattr(var_c.posedit.edit, 'alt'):
                        _, _, _, ref, alt = allele_creator.duplication(
                            chrom,
                            start-1,
                            end,
                            duplicated=ref
                        )
                        vcf_data.update({
                            'pos': start,
                            'ref': ref,
                            'alt': alt
                        })
                    # del
                    elif alt is None:
                        _, _, _, ref, alt = allele_creator.deletion(
                            chrom,
                            start-1,
                            end,
                            deleted=ref
                        )
                        vcf_data.update({
                            'pos': start-1,
                            'ref': ref,
                            'alt': alt
                        })
                    # ins
                    elif ref is None:
                        _, _, _, ref, alt = allele_creator.insertion(
                            chrom,
                            start-1,
                            end,
                            inserted=alt
                        )
                        vcf_data.update({
                            'pos': start,
                            'ref': ref,
                            'alt': alt
                        })

                    # delins
                    elif len(ref) > 1 or len(alt) > 1:
                        _, _, _, ref, alt = allele_creator.indel(
                            chrom,
                            start-1,
                            end,
                            inserted=alt,
                            deleted=ref,
                        )
                        vcf_data.update({
                            'pos': start-1,
                            'ref': ref,
                            'alt': alt
                        })

                    # SNP
                    elif len(ref) == 1 and len(alt) == 1:
                        vcf_data.update({
                            'pos': start,
                            'ref': ref,
                            'alt': alt
                        })

                    vcf_writer.write_data(vcf_data)
                except:
                    logging.error("Error while processing {}".format(fields))


def find_outputdir(given_path, input_file):
    if given_path:
        return given_path
    else:
        return os.path.abspath(os.path.dirname(input_file))


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description="""Deposit variants and genotypes from a VCF file into varDB.""")
    parser.add_argument('variantlist', metavar='N', type=str, nargs=1,
                        help='TSV file with variant assessments')
    parser.add_argument("--reference", action="store", dest="reference", required=True, help="Path to genome reference file")
    parser.add_argument("--outputdir", action="store", dest="outputDirectoryPath", required=False,
                        help="Directory for output files (will overwrite existing files). Filename will have the .vcf extension")

    args = parser.parse_args()
    input_filename = args.variantlist[0]
    output_dir = find_outputdir(args.outputDirectoryPath, input_filename)
    output_file = os.path.join(output_dir, '{base_filename}.vcf'.format(base_filename=os.path.basename(input_filename)))

    spe = ExcelExporter(args.reference)
    with open(input_filename) as f:
        lines = f.readlines()

    spe.parse_exported(lines, output_file)
