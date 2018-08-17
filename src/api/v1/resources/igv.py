import os
import mimetypes
import json
from cStringIO import StringIO
from collections import OrderedDict

from flask import request, Response, send_file
from sqlalchemy import tuple_

from api import ApiError
from api.config import config

from vardb.datamodel import sample, gene, allele

from api.v1.resource import LogRequestResource
from api.util.util import authenticate, rest_filter
from api.util.alleledataloader import AlleleDataLoader

IGV_DEFAULT_TRACK_CONFIGS = {
    "vcf": {
        "format": "vcf",
        "visibilityWindow": 1e9, # Whole chromosome
        "order": 200
    },
    "bam": {
        "format": "bam",
        "colorBy": 'strand',
        'alignmentRowHeight': 10,
        "visibilityWindow": 20000,
        "order": 300
    },
    "bed": {
        "format": "bed",
        "displayMode": "EXPANDED",
        "order": 100
    }
}

def get_range(request):

    range_header = request.headers.get('Range', None)

    if range_header is None:
        return None, None

    if ',' in range_header:
        raise RuntimeError("Multiple ranges not supported.")

    if range_header:
        range = range_header.split('bytes=', 1)[1].split('-', 1)

        start = int(range[0])
        if not range[1] == '':
            end = int(range[1])
        else:
            end = None
    elif 'start' in request.args:
        # Try GET params instead
        start = int(request.args.get('start'))
        end = int(request.args.get('end'))
    else:
        start = end = None
    return start, end


def get_partial_response(path, start, end):
    size = os.path.getsize(path)
    data = None
    with open(path, 'rb') as f:
        f.seek(start)
        if end:
            data = f.read(end - start + 1)
        else:
            data = f.read()

    print len(data)
    rv = Response(
        data,
        206,
        mimetype=mimetypes.guess_type(path)[0],
        direct_passthrough=True
    )
    if end:
        if end - start + 1 > size:
            end = size - start - 1
        rv.headers.add('Content-Length', '{0}'.format(end - start + 1, size))
        rv.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(start, end, size))
    else:
        rv.headers.add('Content-Length', '{0}'.format(size))
        rv.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(start, size - 1, size))
    return rv


class IgvResource(LogRequestResource):
    @authenticate()
    def get(self, session, filename, user=None):
        if 'IGV_DATA' not in os.environ:
            raise ApiError("Missing IGV data location (env: $IGV_DATA).")

        if filename not in config['igv']['valid_resource_files']:
            raise ApiError("File is not in list of permitted accessible files.")

        final_path = os.path.join(os.environ['IGV_DATA'], filename)

        start, end = get_range(request)
        if start is None:
            return send_file(final_path)
        else:
            return get_partial_response(final_path, start, end)


def transcripts_to_gencode(transcripts):
    """Write transcripts out in the format expected by igv"""
    template = '{chr}\t{tx_start}\t{tx_end}\t{name}\t1000.0\t{strand}\t{cds_start}\t{cds_end}\t.\t{num_exons}\t{exon_lengths}\t{exon_starts}\tfoo\n'

    data = StringIO()
    for t in transcripts:
        def _modify_0_based(t):
            t.exon_starts = [es+1 for es in t.exon_starts]
            t.exon_ends = [ee+1 for ee in t.exon_ends]
            t.tx_start += 1
            t.tx_end += 1
            t.cds_start += 1
            t.cds_end += 1
            return t
        t = _modify_0_based(t)

        exon_lengths = [str(e-s) for s, e in zip(t.exon_starts, t.exon_ends)]
        relative_exon_starts = [str(s-t.tx_start) for s in t.exon_starts]

        data.write(template.format(
            chr=t.chromosome,
            tx_start=t.tx_start,
            tx_end=t.tx_end,
            name="{gene}({tx})".format(
                gene=t.gene.hgnc_symbol, tx=t.transcript_name),
            strand=t.strand,
            cds_start=t.tx_start,
            cds_end=t.tx_end,
            num_exons=len(t.exon_starts),
            exon_lengths=",".join(exon_lengths)+",",
            exon_starts=",".join(relative_exon_starts)+","
        ))

    data.seek(0)
    return data


class GencodeGenepanelResource(LogRequestResource):
    @authenticate()
    def get(self, session, gp_name, gp_version, user=None):
        gp = session.query(
            gene.Genepanel
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version) == (
                gp_name, gp_version)
        ).one()

        gencode = transcripts_to_gencode(gp.transcripts)

        return send_file(gencode)


class AnalysisVariantTrack(LogRequestResource):
    @authenticate()
    @rest_filter
    def get(self, session, analysis_id, sample_id, rest_filter=None, user=None):
        allele_ids = [int(aid) for aid in rest_filter['allele_ids']]

        alleles = session.query(allele.Allele).filter(
            allele.Allele.id.in_(allele_ids)
        ).all()

        analysis = session.query(sample.Analysis).filter(
            sample.Analysis.id == analysis_id
        ).one()

        sample_name = session.query(sample.Sample.identifier).filter(
            sample.Sample.id == sample_id
        ).scalar()

        adl = AlleleDataLoader(session)
        allele_objs = adl.from_objs(alleles,
                                    genepanel=analysis.genepanel,
                                    include_allele_assessment=False,
                                    include_genotype_samples=[sample_id],
                                    include_allele_report=False,
                                    include_custom_annotation=False,
                                    include_reference_assessments=False)

        VCF_HEADER_TEMPLATE = "\n".join([
            '##fileformat=VCFv4.1',
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{}"
        ])+"\n"
        VCF_LINE_TEMPLATE = "{chr}\t{pos}\t{id}\t{ref}\t{alt}\t{qual}\t{filter_status}\t{info}\t{genotype_format}\t{genotype_data}\n"

        header = VCF_HEADER_TEMPLATE.format(sample_name)
        data = StringIO()
        data.write(header)

        for a in sorted(allele_objs, key=lambda x: (int(x["chromosome"]) if x["chromosome"].isdigit() else x["chromosome"], int(x["vcf_pos"]))):
            chr = a["chromosome"]
            pos = a["vcf_pos"]
            ref = a["vcf_ref"]
            alt = a["vcf_alt"]
            sample_data = next(s for s in a["samples"] if s["id"] == sample_id)
            dbsnp = set(sum([t.get("dbsnp", []) for t in a["annotation"]["transcripts"]
                             if t["transcript"] in a["annotation"]["filtered_transcripts"]], []))

            genotype_data = sample_data["genotype"]
            qual = genotype_data["variant_quality"]

            gt = '1/1' if genotype_data["homozygous"] else '0/1'


            quality_data = OrderedDict()
            quality_data["GT"] = '1/1' if genotype_data["homozygous"] else '0/1'

            if len(genotype_data["allele_depth"]) == 2:
                ad_copy = dict(genotype_data["allele_depth"])
                quality_data["DP"] = str(sum(ad_copy.values()))
                quality_data["AD"] = str(ad_copy.pop(
                    "REF"))+","+str(ad_copy.values()[0])

            else:
                ad = None
                dp = None

            quality_data["GQ"] = str(genotype_data["genotype_quality"])
            filter_status = genotype_data["filter_status"]

            quality_format = ":".join(quality_data.keys())
            quality_data = ":".join(quality_data.values())

            # Annotation
            def get_formatted_freq(label, freqs, subpop):
                return "%s=%.5g(%d/%d)" % (label, freqs['freq'][subpop], freqs['count'][subpop], freqs['num'][subpop])

            info = []
            gnomad_exomes = a["annotation"]["frequencies"].get("GNOMAD_EXOMES")
            if gnomad_exomes:
                info.append(get_formatted_freq(
                    "GNOMAD_EXOMES", gnomad_exomes, 'G'))

            gnomad_genomes = a["annotation"]["frequencies"].get(
                "GNOMAD_GENOMES")
            if gnomad_genomes:
                info.append(get_formatted_freq(
                    "GNOMAD_GENOMES", gnomad_genomes, 'G'))

            # indb = a["annotation"]["frequencies"].get("inDB")
            # if indb:
            #     info.append(get_formatted_freq("OUSWES", indb, 'OUSWES'))

            data.write(VCF_LINE_TEMPLATE.format(
                chr=chr,
                pos=pos,
                id=",".join(dbsnp) if dbsnp else ".",
                ref=ref,
                alt=alt,
                qual=qual,
                filter_status=filter_status,
                info=";".join(info) if info else ".",
                genotype_format=quality_format,
                genotype_data=quality_data
            ))
        data.seek(0)

        return send_file(data)



def get_analysis_tracks(analysis_id, analysis_name):
    if 'ANALYSES_PATH' in os.environ:
        return []
    analyses_path = os.environ["ANALYSES_PATH"]
    tracks_folder = os.path.join(analyses_path, analysis_name, "tracks")
    if not os.path.isdir(tracks_folder):
        return []

    index_extensions = ['.fai', '.idx', '.index', '.bai', '.tbi']
    config_extensions = ['.json', '.config']

    track_files = [f for f in os.listdir(tracks_folder) if not any(f.endswith(ext) for ext in index_extensions+config_extensions)]
    print os.listdir(tracks_folder)
    tracks = []
    for t in track_files:
        config_file = next((t+ext for ext in config_extensions if os.path.isfile(os.path.join(tracks_folder, t+ext))), None)
        if config_file:
            try:
                config = json.load(open(os.path.join(tracks_folder, config_file)))
            except ValueError:
                config = {}
                pass

        extension = os.path.splitext(t)
        filetype = os.path.splitext(t)[1][1:] if os.path.splitext(t)[1] != '.gz' else os.path.splitext(os.path.splitext(t)[0])[1][1:]

        track_config = json.loads(json.dumps(IGV_DEFAULT_TRACK_CONFIGS[filetype]))
        track_config.update(config)
        track_config["url"] = "/api/v1/igv/tracks/{}/{}".format(analysis_id, t)
        track_config.setdefault('name', t)

        def possible_index_files(f):
            for ext in index_extensions:
                yield f+ext
                if os.path.splitext(f)[1] in ['.gz', '.bam']:
                    yield os.path.splitext(f)[0]+ext

        index_file = next((f for f in possible_index_files(t) if os.path.isfile(os.path.join(tracks_folder, f))), None)
        if index_file:
            track_config["indexed"] = True
            track_config["indexURL"] = "/api/v1/igv/tracks/{}/{}".format(analysis_id, index_file)
        else:
            track_config["indexed"] = False

        tracks.append(track_config)
    return tracks


class AvailableTracks(LogRequestResource):
    @authenticate()
    def get(self, session, analysis_id, user=None):
        analysis_name = session.query(
            sample.Analysis.name
        ).filter(
            sample.Analysis.id == analysis_id
        ).scalar()

        analysis_tracks = get_analysis_tracks(analysis_id, analysis_name)
        print json.dumps(analysis_tracks, indent=4)
        return analysis_tracks


class AnalysisTrack(LogRequestResource):
    @authenticate()
    def get(self, session, analysis_id, filename, user=None):
        analysis_name = session.query(
            sample.Analysis.name
        ).filter(
            sample.Analysis.id == analysis_id
        ).scalar()

        path = os.path.join(os.environ['ANALYSES_PATH'], analysis_name, "tracks", filename)

        start, end = get_range(request)

        if start is None:
            return send_file(path)
        else:
            return get_partial_response(path, start, end)

