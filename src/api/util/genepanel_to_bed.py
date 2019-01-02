from collections import OrderedDict
from sqlalchemy import tuple_

from vardb.datamodel import gene
from typing import Dict


BED_COLUMNS: Dict = OrderedDict()
BED_COLUMNS["#chromosome"] = lambda t: t.chromosome
BED_COLUMNS["txStart"] = lambda t: str(t.tx_start)
BED_COLUMNS["txEnd"] = lambda t: str(t.tx_end)


def genepanel_to_bed(session, genepanel_name, genepanel_version):
    genepanel = (
        session.query(gene.Genepanel)
        .filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version)
            == (genepanel_name, genepanel_version)
        )
        .one()
    )

    bed_data = "\t".join(list(BED_COLUMNS.keys()))

    for t in genepanel.transcripts:
        row = [v(t) for v in list(BED_COLUMNS.values())]
        bed_data += "\n" + "\t".join(row)

    return bed_data
