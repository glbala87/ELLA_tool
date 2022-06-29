import copy
import itertools
import json
import logging
import os
import re
import typing
from enum import auto
from typing import Any, Dict, List, Pattern

from api import ApiError
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import IgvTrackConfigListResponse
from api.util.types import StrEnum
from api.util.util import authenticate
from api.v1.resource import LogRequestResource
from flask import request
from sqlalchemy.orm import Session
from vardb.datamodel import sample, user

log = logging.getLogger(__name__)


class TrackType(StrEnum):
    bam = auto()
    bed = auto()
    bedgz = auto()
    bigBed = auto()
    bigWig = auto()
    cram = auto()
    gff3gz = auto()
    gtfgz = auto()
    vcf = auto()
    vcfgz = auto()


class TrackSuffixType:
    __slots__ = ["type", "track_suffix", "idx_suffixes"]

    def __init__(self, track_suffix: str, idx_suffixes: List[str], type: TrackType):
        self.type = type
        self.track_suffix = track_suffix
        self.idx_suffixes = idx_suffixes


VALID_TRACK_TYPES = [
    TrackSuffixType(".bam", [".bam.bai", ".bai"], TrackType.bam),
    TrackSuffixType(".bed", [], TrackType.bed),
    TrackSuffixType(".bed.gz", [".bed.gz.tbi"], TrackType.bedgz),
    TrackSuffixType(".bb", [], TrackType.bigBed),
    TrackSuffixType(".bigBed", [], TrackType.bigBed),
    TrackSuffixType(".bw", [], TrackType.bigWig),
    TrackSuffixType(".bigWig", [], TrackType.bigWig),
    TrackSuffixType(".cram", [".cram.crai", ".crai"], TrackType.cram),
    TrackSuffixType(".gff3.gz", [".gff3.gz.tbi"], TrackType.gff3gz),
    TrackSuffixType(".gtf.gz", [".gtf.gz.tbi"], TrackType.gtfgz),
    TrackSuffixType(".vcf", [], TrackType.vcf),
    TrackSuffixType(".vcf.gz", [".vcf.gz.tbi"], TrackType.vcfgz),
]


class TrackSourceType(StrEnum):
    DYNAMIC = "DYNAMIC"
    STATIC = "STATIC"
    ANALYSIS = "ANALYSIS"


DYNAMIC_TRACK_PATHS = ["variants", "classifications", "genepanel", "regions_of_interest"]


class TrackCfgKey(StrEnum):
    APPLIED_RULES = auto()
    LIMIT_TO_GROUPS = auto()
    URL = auto()
    IGV = auto()


class TrackCfgIgvKey(StrEnum):
    NAME = auto()
    URL = auto()
    INDEXURL = "indexURL"


class TrackSrcId:
    """stores track ID and actual path on fs"""

    def __init__(self, source_type: TrackSourceType, rel_path: str):
        def _track_id(track_source_id: TrackSourceType, rel_track_path: str) -> str:
            return f"{track_source_id}/{rel_track_path}"

        self.source_type = source_type
        self.id = _track_id(source_type, rel_path)
        self.rel_path = rel_path

    @staticmethod
    def from_rel_paths(track_source_id: TrackSourceType, rel_path: List[str]):
        return [TrackSrcId(track_source_id, sid) for sid in rel_path]

    @staticmethod
    def rm_track_source(tid):
        def _rm_prefix(s: str, pfx: str) -> str:
            if s.startswith(pfx):
                return s[len(pfx) :]
            return s

        for src_id in TrackSourceType:
            tid = _rm_prefix(tid, f"{src_id}/")
        return tid


def load_raw_config(track_ids: List[TrackSrcId], usergroup_name: str) -> Dict[str, Any]:
    """Takes a list of track IDs and returns their raw config.
       This is done by checking if the tracks exist and by appling all config rules.
       The function is used in two siutations:
    - API call for the track config: All tracks know in ella are passed in as agruments.
        Only configs for accessible tracks are returned. Some postprocessing is required
        before sending it from the API (interpolate urls, add default values) - Hence the "raw"
    - API call for a single track: A single track Id is passed in. Used to check if the
        track ID is accessible by the requesting user. If it's not,
        load_raw_config() will return {}
    """
    # try load custom config
    ella_cfg_path = os.path.join(get_igv_data_dir(), "track_config.json")
    if not os.path.isfile(ella_cfg_path):
        # try default config
        ella_cfg_path = os.path.join(get_igv_data_dir(), "track_config_default.json")
    # valid file?
    if not os.path.isfile(ella_cfg_path):
        raise ApiError(f"IGV track config ('{ella_cfg_path}') not found")
    with open(ella_cfg_path) as f:
        inp_cfg = json.load(f)
    # are keys valid regular expressions?
    compiled_regexes: Dict[str, Pattern] = {}
    for inp_cfg_id_pattern in inp_cfg:
        try:
            compiled_regexes[inp_cfg_id_pattern] = re.compile(inp_cfg_id_pattern)
        except re.error as e:
            log.error(e)
            raise ApiError(
                f"IGV track config key ('{inp_cfg_id_pattern}') is not a valid regular expression"
            )

    # TODO: load individual configs here?

    # apply configs to tracks (one config per track)
    track_cfgs = {}
    for track_src_id in track_ids:
        dst_cfg: Dict[TrackCfgKey, Any] = {
            TrackCfgKey.APPLIED_RULES: [],
            TrackCfgKey.IGV: {TrackCfgIgvKey.NAME: track_src_id.id},
        }
        # for each track, integrate maching configs
        for inp_cfg_id_pattern, inp_cfg_value in inp_cfg.items():
            inp_cfg_value = copy.deepcopy(inp_cfg_value)
            # try to match id
            if not compiled_regexes[inp_cfg_id_pattern].match(track_src_id.id):
                continue
            # merge igv config separately to not overwite its configs
            if TrackCfgKey.IGV in inp_cfg_value:
                dst_cfg[TrackCfgKey.IGV] = {
                    **dst_cfg[TrackCfgKey.IGV],
                    **inp_cfg_value[TrackCfgKey.IGV],
                }
                del inp_cfg_value[TrackCfgKey.IGV]
            # need to deepcopy because we will modify the object
            dst_cfg = {**dst_cfg, **inp_cfg_value}
            dst_cfg[TrackCfgKey.APPLIED_RULES].append(inp_cfg_id_pattern)
        track_cfgs[track_src_id.id] = dst_cfg
    # filter tracks by user
    for track_id in list(track_cfgs):  # creates copy of keys as we are deleting some in the loop
        cfg = track_cfgs[track_id]
        keep_track = True
        # TODO: keep track if user == admin (maybe also keep LIMIT_TO_GROUPS field)
        keep_track = keep_track and TrackCfgKey.LIMIT_TO_GROUPS in cfg.keys()
        keep_track = keep_track and (
            cfg[TrackCfgKey.LIMIT_TO_GROUPS]
            is None  # "LIMIT_TO_GROUPS: null" enables public access
            or any(g == usergroup_name for g in cfg[TrackCfgKey.LIMIT_TO_GROUPS])
        )
        # rm group key
        cfg.pop(TrackCfgKey.LIMIT_TO_GROUPS, None)
        # rm track?
        if not keep_track:
            del track_cfgs[track_id]
    return track_cfgs


def get_igv_data_dir() -> str:
    igv_data_path = os.environ.get("IGV_DATA")
    if not igv_data_path or not os.path.isdir(igv_data_path):
        raise ApiError(f"invalid IGV_DATA path ('{igv_data_path}')")
    return igv_data_path


def get_igv_tracks_dir() -> str:
    igv_data_path = get_igv_data_dir()
    tracks_path = os.path.join(igv_data_path, "tracks")
    if not os.path.isdir(tracks_path):
        raise ApiError(f"IGV track path ('{tracks_path}') not found")
    return tracks_path


def get_analysis_track_dir(analysis_name: str) -> typing.Optional[str]:
    analyses_path = os.environ.get("ANALYSES_PATH")
    if not analyses_path or not os.path.isdir(analyses_path):
        raise ApiError(f"invalid ANALYSES_PATH path ('{analyses_path}')")
    tracks_path = os.path.join(analyses_path, analysis_name, "tracks")
    if not os.path.isdir(tracks_path):
        # raise ApiError(f"analysis track path ('{tracks_path}') not found")
        return None
    return tracks_path


def search_rel_track_paths(tracks_path: typing.Optional[str]) -> List[str]:
    if tracks_path is None:
        # called should check if path is valied (non-existent anaylysis folder is ok)
        return []

    valid_extentions = [t.track_suffix for t in VALID_TRACK_TYPES]

    # only files with track data
    def _filter_ext(f):
        return any(f.endswith(ext) for ext in valid_extentions)

    # filter files and normalize path relative to tracks_path
    def _get_rel_path(p):
        (root, dirs, files) = p
        return [
            os.path.normpath(os.path.join(os.path.relpath(root, tracks_path), f))
            for f in filter(_filter_ext, files)
        ]

    # flatten (list of files by dir) to plain list
    return list(itertools.chain(*map(_get_rel_path, os.walk(tracks_path))))


class AnalysisTrackList(LogRequestResource):
    @authenticate()
    @validate_output(IgvTrackConfigListResponse)
    def get(self, session: Session, analysis_id: int, user: user.User):
        # resolve some stuff that we will need later
        analysis_name, genepanel_name, genepanel_version = (
            session.query(
                sample.Analysis.name,
                sample.Analysis.genepanel_name,
                sample.Analysis.genepanel_version,
            )
            .filter(sample.Analysis.id == analysis_id)
            .one()
        )

        def _get_url_vars(track_id) -> Dict[str, str]:
            return {
                "TRACK_FILEPATH": TrackSrcId.rm_track_source(track_id),
                "ANALYSIS_ID": str(analysis_id),
                "GENEPANEL_NAME": genepanel_name,
                "GENEPANEL_VERSION": genepanel_version,
                "ALLELE_IDS": request.args.get("allele_ids", ""),
            }

        track_ids: List[TrackSrcId] = []
        # load all static tracks
        track_ids += TrackSrcId.from_rel_paths(
            TrackSourceType.STATIC, search_rel_track_paths(get_igv_tracks_dir())
        )
        # load specific analysis tracks
        track_ids += TrackSrcId.from_rel_paths(
            TrackSourceType.ANALYSIS, search_rel_track_paths(get_analysis_track_dir(analysis_name))
        )
        # define dynamic tracks
        track_ids += TrackSrcId.from_rel_paths(TrackSourceType.DYNAMIC, DYNAMIC_TRACK_PATHS)

        track_cfgs = load_raw_config(track_ids, user.group.name)

        # reorganize config values
        for track_id, cfg in track_cfgs.items():
            # interpolate urls
            url_var = _get_url_vars(track_id)
            # we require generic urls
            if TrackCfgKey.URL not in cfg:
                raise ApiError(f"no key '{TrackCfgKey.URL}' found for track '{track_id}'")
            for pattern, replacement in url_var.items():
                cfg[TrackCfgIgvKey.URL] = cfg[TrackCfgKey.URL].replace(f"<{pattern}>", replacement)
            # create igv entry if it's missing
            if TrackCfgKey.IGV not in cfg:
                cfg[TrackCfgKey.IGV] = {}
            # write igv url
            igv_cfg = cfg[TrackCfgKey.IGV]
            igv_cfg[TrackCfgIgvKey.URL] = cfg[TrackCfgKey.URL]
            # remove un-interpolated url
            del cfg[TrackCfgKey.URL]
            # default track name
            if TrackCfgIgvKey.NAME not in igv_cfg:
                igv_cfg[TrackCfgIgvKey.NAME] = os.path.basename(track_id).split(".")[0]
            for track_type in VALID_TRACK_TYPES:
                # find track type
                if not track_id.endswith(track_type.track_suffix):
                    continue
                # has index file?
                if len(track_type.idx_suffixes) > 0:
                    igv_cfg[TrackCfgIgvKey.INDEXURL] = igv_cfg[TrackCfgIgvKey.URL] + "?index=1"
                # TODO: search on fs?
                break
        return track_cfgs
