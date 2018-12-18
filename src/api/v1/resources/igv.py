import os
import mimetypes
import json
import logging
from cStringIO import StringIO
from collections import OrderedDict

from flask import request, Response, send_file
from sqlalchemy import tuple_, func

from api import ApiError
from api.config import config

from vardb.datamodel import sample, gene, allele, assessment, user as user_model

from api.v1.resource import LogRequestResource
from api.util.util import authenticate, request_json, logger
from api.util.alleledataloader import AlleleDataLoader

log = logging.getLogger()

IGV_DEFAULT_TRACK_CONFIGS = {
    "vcf": {"format": "vcf", "visibilityWindow": 1e9, "order": 200},  # Whole chromosome
    "bam": {
        "format": "bam",
        "colorBy": "strand",
        "alignmentRowHeight": 12,
        "visibilityWindow": 20000,
        "order": 300,
    },
    "bed": {"format": "bed", "displayMode": "EXPANDED", "order": 100},
}


def get_range(request):

    range_header = request.headers.get("Range", None)

    if range_header is None:
        return None, None

    if "," in range_header:
        raise RuntimeError("Multiple ranges not supported.")

    if range_header:
        range = range_header.split("bytes=", 1)[1].split("-", 1)

        start = int(range[0])
        if not range[1] == "":
            end = int(range[1])
        else:
            end = None
    elif "start" in request.args:
        # Try GET params instead
        start = int(request.args.get("start"))
        end = int(request.args.get("end"))
    else:
        start = end = None
    return start, end


def get_partial_response(path, start, end):
    size = os.path.getsize(path)
    data = None
    with open(path, "rb") as f:
        f.seek(start)
        if end:
            data = f.read(end - start + 1)
        else:
            data = f.read()

    rv = Response(data, 206, mimetype=mimetypes.guess_type(path)[0], direct_passthrough=True)
    if end:
        if end - start + 1 > size:
            end = size - start - 1
        rv.headers.add("Content-Length", "{0}".format(end - start + 1, size))
        rv.headers.add("Content-Range", "bytes {0}-{1}/{2}".format(start, end, size))
    else:
        rv.headers.add("Content-Length", "{0}".format(size))
        rv.headers.add("Content-Range", "bytes {0}-{1}/{2}".format(start, size - 1, size))
    return rv


def transcripts_to_bed(transcripts):
    """Write transcripts as a bed file specialized for display in IGV"""
    template = "{chr}\t{tx_start}\t{tx_end}\t{name}\t1000.0\t{strand}\t{cds_start}\t{cds_end}\t.\t{num_exons}\t{exon_lengths}\t{exon_starts}\tfoo\n"

    data = StringIO()
    for t in transcripts:
        exon_lengths = [str(e - s) for s, e in zip(t.exon_starts, t.exon_ends)]
        relative_exon_starts = [str(s - t.tx_start) for s in t.exon_starts]

        data.write(
            template.format(
                chr=t.chromosome,
                tx_start=t.tx_start,
                tx_end=t.tx_end,
                name="{gene}({tx})".format(gene=t.gene.hgnc_symbol, tx=t.transcript_name),
                strand=t.strand,
                cds_start=t.tx_start,
                cds_end=t.tx_end,
                num_exons=len(t.exon_starts),
                exon_lengths=",".join(exon_lengths) + ",",
                exon_starts=",".join(relative_exon_starts) + ",",
            )
        )

    data.seek(0)
    return data


def get_classification_bed(session):

    result = 'track name="Classifications" description="ella classifications" itemRgb="On"\n'

    template = """{chrom}\t{start}\t{end}\t{name}\t0\t-\t{start}\t{end}\t{color}"""
    all_aa = (
        session.query(
            allele.Allele.chromosome,
            allele.Allele.start_position,
            allele.Allele.open_end_position,
            assessment.AlleleAssessment.classification,
        )
        .join(assessment.AlleleAssessment)
        .filter(assessment.AlleleAssessment.date_superceeded.is_(None))
        .all()
    )

    COLORS = {"1": "#76B100", "2": "#6BA100", "3": "#FFAA3C", "4": "#FE5B5B", "5": "#D00000"}

    lines = []
    for chrom, start, end, classification in all_aa:
        lines.append(
            template.format(
                chrom=chrom,
                start=start,
                end=end,
                name=classification,
                color=COLORS.get(classification, "#007ED0"),
            )
        )
    result += "\n".join(lines)
    return result


def get_allele_vcf(session, analysis_id, allele_ids):
    if not allele_ids:
        return None

    alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(allele_ids)).all()

    analysis = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()

    adl = AlleleDataLoader(session)
    allele_objs = adl.from_objs(
        alleles,
        analysis_id=analysis.id,
        genepanel=analysis.genepanel,
        include_allele_assessment=False,
        include_allele_report=False,
        include_custom_annotation=False,
        include_reference_assessments=False,
    )

    VCF_HEADER_TEMPLATE = (
        "\n".join(
            ["##fileformat=VCFv4.1", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{}"]
        )
        + "\n"
    )
    VCF_LINE_TEMPLATE = "{chr}\t{pos}\t{id}\t{ref}\t{alt}\t{qual}\t{filter_status}\t{info}\t{genotype_format}\t{genotype_data}\n"

    sample_names = sorted(list(set([s["identifier"] for a in allele_objs for s in a["samples"]])))
    data = VCF_HEADER_TEMPLATE.format("\t".join(sample_names))

    for a in allele_objs:
        chr = a["chromosome"]
        pos = a["vcf_pos"]
        ref = a["vcf_ref"]
        alt = a["vcf_alt"]
        qual = "N/A"
        filter_status = "N/A"

        genotype_data = {"GT": []}  # Per sample entry
        for sample_name in sample_names:
            sample_data = next((s for s in a["samples"] if s["identifier"] == sample_name), None)
            if not sample_data:
                genotype_data["GT"] = "./."
                continue

            sample_genotype = sample_data["genotype"]

            # We can just overwrite these, will be same for all samples
            qual = sample_genotype["variant_quality"]
            filter_status = sample_genotype["filter_status"]

            genotype_data["GT"] = "1/1" if sample_genotype["type"] == "Homozygous" else "0/1"

        # Annotation
        info = []
        genotype_data_keys = sorted(genotype_data.keys())
        data += VCF_LINE_TEMPLATE.format(
            chr=chr,
            pos=pos,
            id=".",
            ref=ref,
            alt=alt,
            qual=qual,
            filter_status=filter_status,
            info=";".join(info) if info else ".",
            genotype_format=":".join(genotype_data_keys),
            genotype_data=":".join([genotype_data[k] for k in genotype_data_keys]),
        )
    return data


class IgvSearchResource(LogRequestResource):
    @authenticate()
    def get(self, session, user=None):

        term = request.args.get("q")
        if not term:
            return []

        # Try gene first, then transcript name
        # Make sure to use index for the symbol name
        gene_matches = (
            session.query(gene.Gene.hgnc_id)
            .filter(func.lower(gene.Gene.hgnc_symbol).like(term.lower() + "%"))
            .limit(5)
            .all()
        )

        # If we have a match, get the matching transcript locations
        if gene_matches:
            gene_results = (
                session.query(
                    gene.Transcript.chromosome, gene.Transcript.tx_start, gene.Transcript.tx_end
                )
                .join(gene.Gene)
                .filter(gene.Gene.hgnc_id.in_(gene_matches))
                .limit(10)
                .all()
            )

            results = list()
            for r in gene_results:
                results.append({"chromosome": r.chromosome, "start": r.tx_start, "end": r.tx_end})
            return results
        else:
            transcripts_results = (
                session.query(
                    gene.Transcript.chromosome, gene.Transcript.tx_start, gene.Transcript.tx_end
                )
                .filter(gene.Transcript.transcript_name.like(term + "%"))
                .limit(10)
                .all()
            )

            results = list()
            for r in transcripts_results:
                results.append({"chromosome": r.chromosome, "start": r.tx_start, "end": r.tx_end})
            return results


class GenepanelBedResource(LogRequestResource):
    @authenticate()
    def get(self, session, gp_name, gp_version, user=None):
        gp = (
            session.query(gene.Genepanel)
            .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version) == (gp_name, gp_version))
            .one()
        )

        gencode = transcripts_to_bed(gp.transcripts)

        return send_file(gencode)


class ClassificationResource(LogRequestResource):
    @authenticate()
    @logger(exclude=True)
    def get(self, session, user=None):
        data = StringIO()
        data.write(get_classification_bed(session))
        data.seek(0)
        return send_file(data)


class AnalysisVariantTrack(LogRequestResource):
    @authenticate()
    @logger(exclude=True)
    def get(self, session, analysis_id, user=None):
        allele_ids = [int(aid) for aid in request.args.get("allele_ids", "").split(",")]
        data = StringIO()
        data.write(get_allele_vcf(session, analysis_id, allele_ids))
        data.seek(0)
        return send_file(data)


def _search_path_for_tracks(tracks_path, url_func):

    index_extensions = [".fai", ".idx", ".index", ".bai", ".tbi"]

    track_files = [
        f
        for f in os.listdir(tracks_path)
        if not any(f.endswith(ext) for ext in index_extensions + [".json"])
    ]
    tracks = []
    for t in track_files:
        try:
            config_file_path = os.path.join(tracks_path, t + ".json")
            config = dict()
            if os.path.isfile(config_file_path):
                try:
                    config = json.load(open(os.path.join(tracks_path, config_file_path)))
                except ValueError:
                    pass

            filetype = (
                os.path.splitext(t)[1][1:]
                if os.path.splitext(t)[1] != ".gz"
                else os.path.splitext(os.path.splitext(t)[0])[1][1:]
            )
            track_config = json.loads(json.dumps(IGV_DEFAULT_TRACK_CONFIGS[filetype]))
            track_config.update(config)
            track_config["id"] = t
            track_config["url"] = url_func(t)
            if "name" not in track_config:
                track_config["name"] = t

            def possible_index_files(f):
                for ext in index_extensions:
                    yield f + ext
                    if os.path.splitext(f)[1] in [".gz", ".bam"]:
                        yield os.path.splitext(f)[0] + ext

            index_file = next(
                (
                    f
                    for f in possible_index_files(t)
                    if os.path.isfile(os.path.join(tracks_path, f))
                ),
                None,
            )
            if index_file:
                track_config["indexed"] = True
                track_config["indexURL"] = url_func(index_file)
            else:
                track_config["indexed"] = False

            tracks.append(track_config)
        except Exception:
            log.exception("Something went wrong when loading track file {}".format(t))

    return tracks


def _get_global_tracks_path():
    igv_data_path = os.environ.get("IGV_DATA")
    if not igv_data_path:
        return None
    global_tracks_path = os.path.join(igv_data_path, "tracks")
    if os.path.isdir(global_tracks_path):
        return global_tracks_path
    return None


def _get_usergroup_tracks_path(groupname):
    igv_data_path = os.environ.get("IGV_DATA")
    if not igv_data_path:
        return None
    user_tracks_path = os.path.join(igv_data_path, "usergroups", groupname, "tracks")
    if os.path.isdir(user_tracks_path):
        return user_tracks_path
    return None


def _get_analysis_tracks_path(analysis_name):
    analyses_path = os.environ.get("ANALYSES_PATH")
    if not analyses_path:
        return None
    analysis_tracks_path = os.path.join(analyses_path, analysis_name, "tracks")
    if os.path.isdir(analysis_tracks_path):
        return analysis_tracks_path
    return None


def get_global_tracks():
    global_tracks_path = _get_global_tracks_path()
    if not global_tracks_path:
        return []

    def url_func(name):
        return "/api/v1/igv/tracks/global/{}".format(name)

    return _search_path_for_tracks(global_tracks_path, url_func)


def get_user_tracks(user):
    user_tracks_path = _get_usergroup_tracks_path(user.group.name)
    if not user_tracks_path:
        return []

    def url_func(name):
        return "/api/v1/igv/tracks/usergroups/{}/{}".format(user.group.id, name)

    return _search_path_for_tracks(user_tracks_path, url_func)


def get_analysis_tracks(analysis_id, analysis_name):
    analysis_tracks_path = _get_analysis_tracks_path(analysis_name)
    if not analysis_tracks_path:
        return []

    def url_func(name):
        return "/api/v1/igv/tracks/analyses/{}/{}".format(analysis_id, name)

    return _search_path_for_tracks(analysis_tracks_path, url_func)


class IgvResource(LogRequestResource):
    @authenticate()
    @logger(exclude=True)
    def get(self, session, filename, user=None):
        if "IGV_DATA" not in os.environ:
            raise ApiError("Missing IGV data location (env: $IGV_DATA).")

        if filename not in config["igv"]["valid_resource_files"]:
            raise ApiError("File is not in list of permitted accessible files.")

        final_path = os.path.join(os.environ["IGV_DATA"], filename)

        start, end = get_range(request)
        if start is None:
            return send_file(final_path)
        else:
            return get_partial_response(final_path, start, end)


class AnalysisTrackList(LogRequestResource):
    @authenticate()
    def get(self, session, analysis_id, user=None):
        analysis_name = (
            session.query(sample.Analysis.name).filter(sample.Analysis.id == analysis_id).scalar()
        )

        result = {
            "global": get_global_tracks(),
            "user": get_user_tracks(user),
            "analysis": get_analysis_tracks(analysis_id, analysis_name),
        }
        return result


class GlobalTrack(LogRequestResource):
    @authenticate()
    @logger(exclude=True)
    def get(self, session, filename, user=None):

        global_tracks_path = _get_global_tracks_path()
        if not global_tracks_path:
            raise ApiError("There are no global tracks.")

        path = os.path.join(global_tracks_path, filename)
        start, end = get_range(request)

        if start is None:
            return send_file(path)
        else:
            return get_partial_response(path, start, end)


class UserGroupTrack(LogRequestResource):
    @authenticate()
    @logger(exclude=True)
    def get(self, session, usergroup_id, filename, user=None):
        usergroup_name = (
            session.query(user_model.UserGroup.name)
            .filter(user_model.UserGroup.id == usergroup_id)
            .scalar()
        )

        user_tracks_path = _get_usergroup_tracks_path(usergroup_name)
        if not user_tracks_path:
            raise ApiError("Requested usergroup id doesn't contain any tracks.")

        path = os.path.join(user_tracks_path, filename)
        start, end = get_range(request)

        if start is None:
            return send_file(path)
        else:
            return get_partial_response(path, start, end)


class AnalysisTrack(LogRequestResource):
    @authenticate()
    @logger(exclude=True)
    def get(self, session, analysis_id, filename, user=None):
        analysis_name = (
            session.query(sample.Analysis.name).filter(sample.Analysis.id == analysis_id).scalar()
        )

        analysis_tracks_path = _get_analysis_tracks_path(analysis_name)
        if not analysis_tracks_path:
            raise ApiError("Requested analysis id doesn't contain any tracks.")

        path = os.path.join(analysis_tracks_path, filename)
        start, end = get_range(request)

        if start is None:
            return send_file(path)
        else:
            return get_partial_response(path, start, end)
