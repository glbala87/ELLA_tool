import os
import typing

from vardb.datamodel import sample
from api.v1.resource import LogRequestResource
from api.util.util import authenticate
from api import ApiError
from enum import Enum, auto
from typing import List, Dict, Any
from flask import request
import fnmatch
import json
import itertools
import copy


class TrackType(Enum):
    bam = auto()
    bed = auto()
    vcf = auto()
    gff3 = auto()
    bigWig = auto()


class TrackSuffixType:
    def __init__(self, track_suffix: str, idx_suffix: typing.Optional[str], type: TrackType):
        self.type = type
        self.track_suffix = track_suffix
        self.idx_suffix = idx_suffix


VALID_TRACK_TYPES = [
    TrackSuffixType(".bed.gz", ".tbi", TrackType.bed),
    TrackSuffixType(".vcf.gz", ".tbi", TrackType.vcf),
    TrackSuffixType(".gff3.gz", ".tbi", TrackType.gff3),
    TrackSuffixType(".bam", ".bai", TrackType.bam),
    TrackSuffixType(".bigWig", None, TrackType.bigWig),
]


class TrackSourceType(Enum):
    DYNAMIC = auto()
    STATIC = auto()
    ANALYSIS = auto()


DYNAMIC_TRACK_PATHS = ["variants", "classifications", "genepanel"]


class TrackCfgKey(Enum):
    applied_rules = auto()
    limit_to_groups = auto()
    url = auto()
    igv = auto()


class TrackCfgIgvKey(Enum):
    name = "name"  # can't use auto() here - mypy compains :(
    url = "url"
    indexURL = "indexURL"


class TrackSrcId:
    """stores track ID and actual path on fs"""

    def __init__(self, source_type: TrackSourceType, rel_path: str):
        def _track_id(track_source_id: TrackSourceType, rel_track_path: str) -> str:
            return f"{{{track_source_id.name}}}/{rel_track_path}"

        self.source_type = source_type
        self.id = _track_id(source_type, rel_path)
        self.rel_path = rel_path

    @staticmethod
    def from_rel_paths(
        track_source_id: TrackSourceType, rel_path: List[str]
    ):  # TODO: need a return type here
        return [TrackSrcId(track_source_id, sid) for sid in rel_path]

    @staticmethod
    def rm_track_source(tid):
        def _rm_prefix(s: str, pfx: str) -> str:
            if s.startswith(pfx):
                return s[len(pfx) :]
            return s

        for src_id in TrackSourceType:
            tid = _rm_prefix(tid, f"{{{src_id.name}}}/")
        return tid


def load_raw_config(track_ids: List[TrackSrcId], user) -> Dict[str, Any]:
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

    # TODO: load individual configs here?

    # apply configs to tracks (one config per track)
    track_cfgs = {}
    for track_src_id in track_ids:
        dst_cfg: Dict[str, Any] = {TrackCfgKey.applied_rules.name: []}
        # for each track, integrate maching configs
        for inp_cfg_id_pattern, inp_cfg_value in inp_cfg.items():
            # try to match id
            if not fnmatch.fnmatch(track_src_id.id, inp_cfg_id_pattern):
                continue
            # need to deepcopy because we will modify the object
            dst_cfg = {**dst_cfg, **copy.deepcopy(inp_cfg_value)}
            dst_cfg[TrackCfgKey.applied_rules.name].append(inp_cfg_id_pattern)
        track_cfgs[track_src_id.id] = dst_cfg
    # filter tracks by user
    for track_id in list(track_cfgs):  # creates copy of keys as we are deleting some in the loop
        cfg = track_cfgs[track_id]
        keep_track = True
        # TODO: keep track if user == admin (maybe also keep limit_to_groups field)
        keep_track = keep_track and TrackCfgKey.limit_to_groups.name in cfg.keys()
        keep_track = keep_track and (
            cfg[TrackCfgKey.limit_to_groups.name]
            is None  # "limit_to_groups: null" enables public access
            or any(g == user.group.name for g in cfg[TrackCfgKey.limit_to_groups.name])
        )
        # rm group key
        cfg.pop(TrackCfgKey.limit_to_groups.name, None)
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
    def get(self, session, analysis_id, user=None):
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

        track_cfgs = load_raw_config(track_ids, user)

        # reorganize config values
        for track_id, cfg in track_cfgs.items():
            # interpolate urls
            url_var = _get_url_vars(track_id)
            # we require generic urls
            if TrackCfgKey.url.name not in cfg:
                raise ApiError(f"no key '{TrackCfgKey.url.name}' found for track '{track_id}'")
            for pattern, replacement in url_var.items():
                cfg[TrackCfgIgvKey.url.name] = cfg[TrackCfgKey.url.name].replace(
                    f"{{{pattern}}}", replacement
                )
            # create igv entry if it's missing
            if TrackCfgKey.igv.name not in cfg:
                cfg[TrackCfgKey.igv.name] = {}
            # write igv url
            igv_cfg = cfg[TrackCfgKey.igv.name]
            igv_cfg[TrackCfgIgvKey.url.name] = cfg[TrackCfgKey.url.name]
            # remove un-interpolated url
            del cfg[TrackCfgKey.url.name]
            # default track name
            if TrackCfgIgvKey.name.name not in igv_cfg:
                igv_cfg[TrackCfgIgvKey.name.name] = os.path.basename(track_id).split(".")[0]
            for track_type in VALID_TRACK_TYPES:
                if not track_id.endswith(track_type.track_suffix):
                    continue
                if track_type.idx_suffix is not None:
                    igv_cfg[TrackCfgIgvKey.indexURL.name] = (
                        igv_cfg[TrackCfgIgvKey.url.name] + "?index=1"
                    )
                break
        return track_cfgs
