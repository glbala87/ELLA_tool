import argparse
import time
import logging

from vardb.datamodel import DB
from .analysis_watcher import AnalysisWatcher
from .genepanel_watcher import GenepanelWatcher


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

POLL_INTERVAL = 30


def start_polling(session, analyses_path, destination_path, genepanels_path):

    gw = GenepanelWatcher(session, genepanels_path)
    aw = AnalysisWatcher(session, analyses_path, destination_path)

    while True:
        try:
            gw.check_and_import()
        except Exception:
            log.exception("An exception occurred while checking for new genepanels.")
        try:
            aw.check_and_import()
        except Exception:
            log.exception("An exception occurred while checking for new analyses.")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Watch a folder for new analyses to import into database."
    )
    parser.add_argument(
        "--analyses", dest="analyses_path", required=True, help="Path to watch for new analyses"
    )
    parser.add_argument(
        "--dest",
        dest="dest",
        required=True,
        help="Destination path into which the processed data will be copied.",
    )
    parser.add_argument(
        "--genepanels",
        dest="genepanels_path",
        required=True,
        help="Path to watch for new genepanels.",
    )

    args = parser.parse_args()

    log.info("Polling for new analyses every: {} seconds".format(POLL_INTERVAL))
    log.info("Polling for new genepanels every: {} seconds".format(POLL_INTERVAL))

    db = DB()
    db.connect()

    start_polling(db.session, args.analyses_path, args.dest, args.genepanels_path)
