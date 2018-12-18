"""distance_computations

Revision ID: 3aa5e573699c
Revises: 6d7548a6dfd9
Create Date: 2018-05-30 11:15:00.392793

"""


# revision identifiers, used by Alembic.
revision = "3aa5e573699c"
down_revision = "6d7548a6dfd9"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import re
import logging

log = logging.getLogger(__name__)

from sqlalchemy.sql import column, table
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.mutable import MutableDict, Mutable
from sqlalchemy.dialects.postgresql import JSONB

# Should match all possible valid HGVSc annotations (without transcript)
# We use the resulting regex groups below in _calculate_distances, to compute distance
# from coding start (for exonic UTR variants), and exon distance (for intronic variants)
# Examples of valid HGVSc:
# c.279G>A
# n.1901_1904delAAGT
# c.248-1_248insA
# c.11712-20dupT
# c.1624+24T>A
# c.*14G>A
# c.-315_-314delAC

HGVSC_DISTANCE_CHECK = [
    r"(?P<c>[cn])\.",  # Coding or non-coding
    r"(?P<utr1>[\*\-]?)",  # UTR direction (asterisk is 5' UTR, minus is 3' UTR),
    r"(?P<p1>[0-9]+)",  # Position (distance into UTR if UTR region)
    r"(?P<pm1>[\-\+]?)",  # Intron direction if variant is intronic
    r"(?P<ed1>([0-9]+)?)",  # Distance from intron if variant is intronic
    r"((?P<region>_)",  # If del/dup/ins, we could have a region, denoted by a '_'. What follows below is only applicable to those cases
    r"(?P<utr2>[\*\-]?)",
    r"(?P<p2>[0-9]+)",
    r"(?P<pm2>[\-\+]?)",
    r"(?P<ed2>([0-9]+)?)",
    r")?",  # End of region
    r"([ACGT]|[BDHKMNRSVWY]|del|dup|ins)",  # All possible options following the position
]
HGVSC_DISTANCE_CHECK_REGEX = re.compile("".join(HGVSC_DISTANCE_CHECK))


def _calculate_distances(hgvsc):
    """Calculate distances from valid HGVSc.
    References:
    Numbering: http://varnomen.hgvs.org/bg-material/numbering/
    Naming: http://varnomen.hgvs.org/bg-material/standards/

    exon_distance denotes distance from exon for intron variants. For exonic variants, this is 0.

    coding_region_distance denotes distance from coding region of the *spliced* gene.
    This only applies to exonic variants. Used for determining distance into UTR-region of a variant.

    Returns (exon_distance, utr_distance)

    Examples:
            hgvsc        | exon_distance | coding_region_distance
    --------------------+---------------+------------------------
        c.279G>A           |             0 |                      0
        n.1901_1904delAAGT |             0 |                      0
        c.248-1_248insA    |             0 |                      0
        c.11712-20dupT     |           -20 |
        c.1624+24T>A       |            24 |
        c.*14G>A           |             0 |                     14
        c.-315_-314delAC   |             0 |                   -314
    """
    match = HGVSC_DISTANCE_CHECK_REGEX.match(hgvsc)
    if not match:
        if hgvsc:
            log.warning("Unable to parse distances from hgvsc: {}".format(hgvsc))
        return None, None

    exon_distance = None
    coding_region_distance = None
    match_data = match.groupdict()

    # Region variants could extend from intron into an exon, e.g. c.*431-1_*431insA
    # The regex would then match on ed1, but not on ed2 (and return distance of -1)
    # However, if it matches on one of them, but not the other, we force the other to be "0"
    def fix_region_distance(d1, d2):
        if d1 or d2:
            d1 = d1 if d1 else "0"
            d2 = d2 if d2 else "0"
            return d1, d2
        else:
            return d1, d2

    if match_data["region"]:
        match_data["ed1"], match_data["ed2"] = fix_region_distance(
            match_data["ed1"], match_data["ed2"]
        )

    def get_distance(pm1, d1, pm2, d2):
        if not (pm1 or pm2):
            # If neither pm1 or pm2 is provided, we are at an exonic variant
            return 0
        elif d1 and not d2:
            # Happens for simple snips, e.g c.123-46A>G or c.*123A>G
            assert not pm2
            return -int(d1) if pm1 == "-" else int(d1)
        elif d1 and d2:
            # Take the minimum of the two, as this is closest position to the exon/coding start
            d = min(int(d1), int(d2))
            if int(d1) == d:
                return -d if pm1 == "-" else d
            else:
                return -d if pm2 == "-" else d
        else:
            raise RuntimeError(
                "Unable to compute distance from ({}, {}), ({}, {})".format(pm1, d1, pm2, d2)
            )

    exon_distance = get_distance(
        match_data["pm1"], match_data["ed1"], match_data["pm2"], match_data["ed2"]
    )

    if exon_distance == 0:
        if (match_data["p1"] and not match_data["utr1"]) or (
            match_data["p2"] and not match_data["utr2"]
        ):
            # Since utr1/utr2 is always shown as either * or - for UTR regions, we know that we are in a coding region
            # if either of those are empty
            coding_region_distance = 0
        else:
            coding_region_distance = get_distance(
                match_data["utr1"], match_data["p1"], match_data["utr2"], match_data["p2"]
            )

    return exon_distance, coding_region_distance


class JSONMutableDict(MutableDict):
    def __setitem__(self, key, value):
        if isinstance(value, collections.Mapping):
            if not isinstance(value, JSONMutableDict):
                value = JSONMutableDict.coerce(key, value)
        elif isinstance(value, list):
            value = JSONMutableList.coerce(key, value)
        dict.__setitem__(self, key, value)
        self.changed()

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        if isinstance(value, dict):
            if not isinstance(value, JSONMutableDict):
                value = JSONMutableDict.coerce(key, value)
                value._parents = self._parents
                dict.__setitem__(self, key, value)
                return value
        elif isinstance(value, list):
            value = JSONMutableList.coerce(key, value)
            value._parents = self._parents
        dict.__setitem__(self, key, value)
        return value

    @classmethod
    def coerce(cls, key, value):
        """Convert plain dictionary to JSONMutableDict."""
        if not isinstance(value, JSONMutableDict):
            if isinstance(value, dict):
                return JSONMutableDict(value)
            return Mutable.coerce(key, value)
        else:
            return value


Annotation = table(
    "annotation",
    column("id", sa.Integer()),
    column("annotations", JSONMutableDict.as_mutable(JSONB)),
)


def upgrade():
    conn = op.get_bind()

    # Drop shadow tables. The trigger will not allow updates of Annotation.c.annotations.
    # Furthermore, the annotationshadowtranscript table will be incorrect after migration.
    op.drop_table("annotationshadowtranscript")
    op.drop_table("annotationshadowfrequency")
    conn.execute(
        sa.sql.text("DROP TRIGGER IF EXISTS annotation_to_annotationshadow on annotation;")
    )
    conn.execute(sa.sql.text("DROP FUNCTION IF EXISTS delete_annotationshadow(integer);"))
    conn.execute(
        sa.sql.text("DROP FUNCTION IF EXISTS insert_annotationshadowfrequency(integer, jsonb);")
    )
    conn.execute(
        sa.sql.text("DROP FUNCTION IF EXISTS insert_annotationshadowtranscript(integer, jsonb);")
    )

    annotations = conn.execute(sa.select(Annotation.c))

    for a in annotations:
        for t in a.annotations.get("transcripts", []):
            hgvsc = t.get("HGVSc")
            if hgvsc:
                exon_distance, coding_region_distance = _calculate_distances(hgvsc)
                t["exon_distance"] = exon_distance
                t["coding_region_distance"] = coding_region_distance

        conn.execute(
            sa.update(Annotation).where(Annotation.c.id == a.id).values(annotations=a.annotations)
        )
    print("!!! Remember to run refresh on shadow tables !!!")


def downgrade():
    raise NotImplementedError("Downgrade not possible")


if __name__ == "__main__":

    def generate_data(hgvsc):
        return {"CSQ": [{"Feature_type": "Transcript", "HGVSc": hgvsc, "Feature": "NM_SOMETHING"}]}

    cases = [
        ("c.4535-213G>T", -213, None),
        ("c.4535+213G>T", 213, None),
        ("c.*35-21G>T", -21, None),
        ("c.-35+21G>T", 21, None),
        ("c.4535+1insAAA", 1, None),
        ("c.4535-1dupTTT", -1, None),
        ("c.4535+0dupTTT", 0, 0),
        ("n.4535+1insAAA", 1, None),
        ("n.4535-1dupTTT", -1, None),
        ("c.4535G>T", 0, 0),
        ("c.4535G>T", 0, 0),
        ("n.4535G>T", 0, 0),
        ("n.4535G>T", 0, 0),
        ("c.*4535G>T", 0, 4535),
        ("c.-4535G>T", 0, -4535),
        ("c.820-131_820-130delAA", -130, None),
        ("n.1901_1904delAAGT", 0, 0),
        ("c.248-1_248insA", 0, 0),
        ("c.248+1_248insA", 0, 0),
        ("c.248_248-1insA", 0, 0),
        ("c.248_248+1insA", 0, 0),
        ("c.248+3_249-8del", 3, None),
        ("c.248-3_249+8del", -3, None),
        ("c.248+8_249-3del", -3, None),
        ("c.248-8_249+3del", 3, None),
        ("c.-315_-314delAC", 0, -314),
        ("c.-264+88_-264+89delTT", 88, None),
        ("c.-264-89_-264-88delTT", -88, None),
        ("c.*264+88_*264+89delTT", 88, None),
        ("c.*264-89_*264-88delTT", -88, None),
        ("c.1597-10_1597-3dupTTATTTAT", -3, None),
        ("c.13+6_14-8dupTTATTTAT", 6, None),
        ("c.13-6_14+8dupTTATTTAT", -6, None),
        ("c.13-8_14+6dupTTATTTAT", 6, None),
        ("c.13+8_14-6dupTTATTTAT", -6, None),
        ("c.*13+6_*14-8dupTTATTTAT", 6, None),
        ("c.*13-6_*14+8dupTTATTTAT", -6, None),
        ("c.*13-8_*14+6dupTTATTTAT", 6, None),
        ("c.*13+8_*14-6dupTTATTTAT", -6, None),
        ("c.-13+6_-14-8dupTTATTTAT", 6, None),
        ("c.-13-6_-14+8dupTTATTTAT", -6, None),
        ("c.-13-8_-14+6dupTTATTTAT", 6, None),
        ("c.-13+8_-14-6dupTTATTTAT", -6, None),
        ("c.*1+6_8dupTTATTTAT", 0, 0),
        ("c.*1-6_8dupTTATTTAT", 0, 0),
        ("c.-1-8_6dupTTATTTAT", 0, 0),
        ("c.-1+8_6dupTTATTTAT", 0, 0),
        ("c.6_-1+8dupTTATTTAT", 0, 0),
        ("c.6_-1-8dupTTATTTAT", 0, 0),
        ("c.8_*1-6dupTTATTTAT", 0, 0),
        ("c.8_*1+6dupTTATTTAT", 0, 0),
        ("c.*-15A>C", None, None),  # Illegal
    ]

    for hgvsc, exon_distance, coding_region_distance in cases:
        ed, cdr = _calculate_distances(hgvsc)
        assert ed == exon_distance, "{} failed {}!={}".format(hgvsc, ed, exon_distance)
        assert cdr == coding_region_distance, "{} failed {}!={}".format(
            hgvsc, cdr, coding_region_distance
        )
