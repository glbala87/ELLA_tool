import os
import mimetypes
import logging
from io import BytesIO
from flask import request, Response, send_file
from sqlalchemy import tuple_, func
from api.config import config
from vardb.datamodel import sample, gene, allele, assessment
from api.v1.resource import LogRequestResource
from api.util.util import authenticate, logger
from datalayer import AlleleDataLoader
from api import ApiError
from . import igvcfg


log = logging.getLogger()

AUTH_ERROR = ApiError("not authorized")


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

    if end is not None:
        end = min(size - 1, end)
    else:
        end = size - 1

    content_length = end - start + 1

    with open(path, "rb") as f:
        f.seek(start)
        data = f.read(content_length)

    rv = Response(data, 206, mimetype=mimetypes.guess_type(path)[0], direct_passthrough=True)
    rv.headers.add("Content-Range", "bytes {0}-{1}/{2}".format(start, end, size))
    return rv


def transcripts_to_bed(transcripts):
    """Write transcripts as a bed file specialized for display in IGV"""
    template = "{chr}\t{tx_start}\t{tx_end}\t{name}\t1000.0\t{strand}\t{cds_start}\t{cds_end}\t.\t{num_exons}\t{exon_lengths}\t{exon_starts}\tfoo\n"

    data = BytesIO()
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
            ).encode()
        )

    data.seek(0)
    return data


def get_classification_gff3(session):

    all_aa = (
        session.query(
            allele.Allele.chromosome,
            allele.Allele.start_position,
            allele.Allele.open_end_position,
            assessment.AlleleAssessment.classification,
            allele.Allele.genome_reference,
            allele.Allele.vcf_pos,
            allele.Allele.vcf_ref,
            allele.Allele.vcf_alt,
            assessment.AlleleAssessment.genepanel_name,
            assessment.AlleleAssessment.genepanel_version,
            assessment.AlleleAssessment.date_created,
        )
        .join(assessment.AlleleAssessment)
        .filter(assessment.AlleleAssessment.date_superceeded.is_(None))
        .all()
    )

    template = (
        "{chrom}\t"
        "ELLA interpretation\t"  # source
        "Classification\t"  # feature
        "{start}\t"
        "{end}\t"
        ".\t"  # score
        ".\t"  # strand
        ".\t"  # frame
        # attributes:
        "Name=Class {class_}"
        "; Assessment={assessment_link}"
        "; Date created={date_created}"
    )

    lines = []
    for (
        chrom,
        start,
        end,
        classification,
        genome_reference,
        vcf_pos,
        vcf_ref,
        vcf_alt,
        genepanel_name,
        genepanel_version,
        date_created,
    ) in all_aa:
        allele_name = f"{chrom}-{vcf_pos}-{vcf_ref}-{vcf_alt}"
        assessment_url = f"/workflows/variants/{genome_reference}/{allele_name}"
        assessment_link = f"<a href='{assessment_url}' target='_blank'>{allele_name}</a>"
        lines.append(
            template.format(
                chrom=chrom,
                start=start,
                end=end,
                class_=classification,
                assessment_link=assessment_link,
                date_created=date_created.strftime("%Y-%m-%d"),
            )
        )
    return "\n".join(lines)


def get_alleles_from_db(session, analysis_id, allele_ids):

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
    return allele_objs


class ChromPos:
    def __init__(self, chr, pos):
        self.chr = chr
        self.pos = pos

    def chr_to_int(self):
        if self.chr == "X":
            return 23
        elif self.chr == "Y":
            return 24
        elif self.chr == "MT":
            return 25
        else:
            return int(self.chr)

    def __lt__(self, other):
        if self.chr == other.chr:
            return self.pos < other.pos
        else:
            return self.chr_to_int() < other.chr_to_int()


class BedLine(ChromPos):
    def __init__(self, chr, pos, end):
        super().__init__(chr, pos)
        self.end = end

    def __str__(self):
        return f"{self.chr}\t{self.pos}\t{self.end}"


def get_regions_of_interest(session, analysis_id, allele_ids):
    if not allele_ids:
        return None

    allele_objs = get_alleles_from_db(session, analysis_id, allele_ids)

    bed_lines = []
    for a in allele_objs:
        chr = a["chromosome"]
        pos = a["start_position"]
        length = a["length"]
        bed_lines.append(BedLine(chr, pos, pos + length))
    bed = "\n".join([str(b) for b in sorted(bed_lines)]) + "\n"
    return bed


class VcfLine(ChromPos):
    def __init__(self, chr, pos, id, ref, alt, qual, filter_status, info, genotype_data):
        super().__init__(chr, pos)
        self.id = id
        self.ref = ref
        self.alt = alt
        self.qual = qual
        self.filter_status = filter_status
        self.info = info
        self.genotype_data = genotype_data

    def sorted_genotype_keys(self):
        SORT_ORDER = {"GT": 1, "CN": 2}
        return sorted(self.genotype_data.keys(), key=lambda genotype_key: SORT_ORDER[genotype_key])

    def __str__(self) -> str:
        VCF_LINE_TEMPLATE = "{chr}\t{pos}\t{id}\t{ref}\t{alt}\t{qual}\t{filter_status}\t{info}\t{genotype_format}\t{genotype_data}\n"
        info_text = ";".join(self.info) if self.info else "."
        genotype_data_keys = self.sorted_genotype_keys()
        genotype_format_text = ":".join(genotype_data_keys)
        genotype_data_text = ":".join([",".join(self.genotype_data[k]) for k in genotype_data_keys])
        return VCF_LINE_TEMPLATE.format(
            chr=self.chr,
            pos=self.pos,
            id=".",
            ref=self.ref,
            alt=self.alt,
            qual=self.qual,
            filter_status=self.filter_status,
            info=info_text,
            genotype_format=genotype_format_text,
            genotype_data=genotype_data_text,
        )


class Vcf:
    def __init__(self, sample_names, data_lines):
        self.sample_names = sample_names
        self.data_lines = data_lines

    def __str__(self) -> str:
        VCF_HEADER_TEMPLATE = (
            "\n".join(
                [
                    "##fileformat=VCFv4.1",
                    '##INFO=<ID=SVTYPE,Number=1,Type=String,Description="Type of structural variant">',
                    '##INFO=<ID=SVLEN,Number=.,Type=Integer,Description="Difference in length between REF and ALT alleles">',
                    '##INFO=<ID=END,Number=1,Type=Integer,Description="End position of the variant described in this record">',
                    '##FORMAT=<ID=CN,Number=.,Type=Integer,Description="Copy Number">',
                    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{}",
                ]
            )
            + "\n"
        )
        data_header = VCF_HEADER_TEMPLATE.format("\t".join(self.sample_names))
        lines_sorted = sorted(self.data_lines)
        vcf_lines = "\n".join([str(l) for l in lines_sorted])
        return data_header + vcf_lines + "\n"


def get_allele_vcf(session, analysis_id, allele_ids):

    allele_objs = get_alleles_from_db(session, analysis_id, allele_ids)
    sample_names = sorted(list(set([s["identifier"] for a in allele_objs for s in a["samples"]])))

    data = []
    for a in allele_objs:
        chr = a["chromosome"]
        pos = a["vcf_pos"]
        ref = a["vcf_ref"]
        alt = a["vcf_alt"]
        qual = "N/A"
        filter_status = "N/A"

        genotype_data = {"GT": [], "CN": []}  # Per sample entry
        for sample_name in sample_names:
            sample_data = next((s for s in a["samples"] if s["identifier"] == sample_name), None)
            if not sample_data:
                genotype_data["GT"].append("./.")
                continue

            sample_genotype = sample_data["genotype"]

            # We can just overwrite these, will be same for all samples
            qual = sample_genotype["variant_quality"]
            filter_status = sample_genotype["filter_status"]
            genotype_data["GT"].append("1/1" if sample_genotype["type"] == "Homozygous" else "0/1")
            if a["caller_type"] == "cnv" and sample_genotype["copy_number"] is not None:
                genotype_data["CN"].append(str(sample_genotype["copy_number"]))
            else:
                genotype_data["CN"].append(".")

        # Annotation
        info = []
        if a["caller_type"] == "cnv":
            change_type = a["change_type"]
            length = a["length"]
            info = [f"SVTYPE={change_type.upper()}", f"SVLEN={length}", f"END={pos + length - 1}"]
        data.append(
            VcfLine(
                chr,
                pos,
                ".",
                ref,
                alt,
                qual,
                filter_status,
                info,
                genotype_data,
            )
        )
    vcf = Vcf(sample_names, data)
    return str(vcf)


class IgvSearchResource(LogRequestResource):
    @authenticate()
    def get(self, session, user=None):

        term = request.args.get("q")
        if not term:
            return []

        # Try gene first, then transcript name
        # Make sure to use index for the symbol name (func.lower)
        # Try exact search first, then fuzzy search
        gene_match = (
            session.query(gene.Gene.hgnc_id)
            .filter(func.lower(gene.Gene.hgnc_symbol) == term.lower())
            .scalar()
        )

        if gene_match is None:
            gene_match = (
                session.query(gene.Gene.hgnc_id)
                .filter(func.lower(gene.Gene.hgnc_symbol).ilike(term.lower() + "%"))
                .order_by(gene.Gene.hgnc_symbol)
                .limit(1)
                .scalar()
            )

        # Base query for finding matching transcripts, with the maximal span available
        tx_query = session.query(
            gene.Transcript.chromosome,
            func.min(gene.Transcript.tx_start).label("start"),
            func.max(gene.Transcript.tx_end).label("end"),
        ).group_by(gene.Transcript.chromosome)

        # If we have a match, get the matching transcript location
        if gene_match is not None:
            locus_result = tx_query.join(gene.Gene).filter(gene.Gene.hgnc_id == gene_match).first()
        else:
            # No match on gene, search for transcript name
            # If term is shorter than nine characters, the transcript is not specified enough
            if len(term) < 9:
                return []
            locus_result = tx_query.filter(gene.Transcript.transcript_name == term.upper()).first()

            # Fuzzy search: find all versions of transcript
            if locus_result is None:
                locus_result = tx_query.filter(
                    gene.Transcript.transcript_name.like(term.upper() + ".%")
                )

            # Fuzzy search: match prefix
            if locus_result is None:
                locus_result = tx_query.filter(
                    gene.Transcript.transcript_name.like(term.upper() + "%")
                )

        if not locus_result:
            return []
        else:
            return [
                {"chromosome": locus_result[0], "start": locus_result[1], "end": locus_result[2]}
            ]


class GenepanelBedResource(LogRequestResource):
    @authenticate()
    def get(self, session, gp_name, gp_version, user=None):
        gp = (
            session.query(gene.Genepanel)
            .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version) == (gp_name, gp_version))
            .one()
        )

        gencode = transcripts_to_bed(gp.transcripts)

        return send_file(gencode, attachment_filename="genepanel.bed")


class ClassificationResource(LogRequestResource):
    @authenticate()
    @logger(exclude=True)
    def get(self, session, user=None):
        data = BytesIO()
        data.write(get_classification_gff3(session).encode())
        data.seek(0)
        return send_file(
            data,
            attachment_filename="classifications.gff3",
            mimetype="text/plain",
            cache_timeout=30 * 60,
        )


class RegionsOfInterestTrack(LogRequestResource):
    @authenticate()
    @logger(exclude=True)
    def get(self, session, analysis_id, user=None):
        allele_ids = [int(aid) for aid in request.args.get("allele_ids", "").split(",")]
        data = BytesIO()
        data.write(get_regions_of_interest(session, analysis_id, allele_ids).encode())
        data.seek(0)
        return send_file(data, attachment_filename="analysis-regions-of-interest.bed")


class AnalysisVariantTrack(LogRequestResource):
    @authenticate()
    @logger(exclude=True)
    def get(self, session, analysis_id, user=None):
        allele_ids = [
            int(aid) for aid in request.args.get("allele_ids", "").split(",") if aid != ""
        ]
        data = BytesIO()
        data.write(get_allele_vcf(session, analysis_id, allele_ids).encode())
        data.seek(0)
        return send_file(data, attachment_filename="analysis-variants.vcf")


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


def _get_index_path(track_path):
    for t in igvcfg.VALID_TRACK_TYPES:
        if not track_path.endswith(t.track_suffix):
            continue
        track_idx_path = track_path + t.idx_suffix
        if not os.path.exists(track_idx_path):
            raise AUTH_ERROR
        return track_idx_path
    raise AUTH_ERROR


class StaticTrack(LogRequestResource):
    @authenticate()
    @logger(exclude=True)
    def get(self, session, filepath, user=None):
        index: bool = request.args.get("index", "") == "1"

        # get track path
        tracks_dir = igvcfg.get_igv_tracks_dir()
        # TODO: avoid directory traversal attack
        track_path = os.path.join(tracks_dir, filepath)

        # check if file exists
        if not os.path.exists(track_path):
            raise AUTH_ERROR  # we don't want unathorized users to know if a file exists

        # check permissins by loading config
        track_src_ids = igvcfg.TrackSrcId.from_rel_paths(igvcfg.TrackSourceType.STATIC, [filepath])
        # load config - for current track
        track_cfg = igvcfg.load_raw_config(track_src_ids, user)
        # we passed one id - we should get one track
        if not len(track_cfg.values()) == 1:
            raise AUTH_ERROR
        # get track
        track_cfg = next(iter(track_cfg))

        if index:
            return send_file(_get_index_path(track_path))

        start, end = get_range(request)
        if start is None:
            return send_file(track_path)
        else:
            return get_partial_response(track_path, start, end)


class AnalysisTrack(LogRequestResource):
    @authenticate()
    @logger(exclude=True)
    def get(self, session, analysis_id, filename, user=None):
        index: bool = request.args.get("index", "") == "1"

        def _get_analysis_tracks_path(analysis_name):
            analyses_path = os.environ.get("ANALYSES_PATH")
            if not analyses_path:
                return None
            analysis_tracks_path = os.path.join(analyses_path, analysis_name, "tracks")
            if os.path.isdir(analysis_tracks_path):
                return analysis_tracks_path
            return None

        analysis_name = (
            session.query(sample.Analysis.name).filter(sample.Analysis.id == analysis_id).scalar()
        )

        analysis_tracks_path = _get_analysis_tracks_path(analysis_name)
        if not analysis_tracks_path:
            raise ApiError("Requested analysis id doesn't contain any tracks.")

        path = os.path.join(analysis_tracks_path, filename)

        if index:
            return send_file(_get_index_path(path))

        start, end = get_range(request)

        if start is None:
            return send_file(path)
        else:
            return get_partial_response(path, start, end)
