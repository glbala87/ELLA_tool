# -*- coding: utf-8 -*-
"""
GenepanelWatcher

Watches a path for new genepanels to import into database.

"""

import os
import logging

from vardb.deposit.deposit_genepanel import DepositGenepanel
from vardb.datamodel import gene

log = logging.getLogger(__name__)


class GenepanelWatcher(object):

    def __init__(self, session, watch_path):
        self.session = session
        self.watch_path = watch_path

    def import_genepanel(self,
                         transcripts_path,
                         phenotypes_path,
                         genepanel_name,
                         genepanel_version):

        deposit_genepanel = DepositGenepanel(self.session)
        deposit_genepanel.add_genepanel(
            transcripts_path,
            phenotypes_path,
            genepanel_name,
            genepanel_version,
            force_yes=True
        )

    def check_and_import(self):
        """
        Poll for new genepanels to process.
        """

        for genepanel_dir in os.listdir(self.watch_path):
            try:
                if not os.path.isdir(os.path.join(self.watch_path, genepanel_dir)):
                    continue

                genepanel_path = os.path.join(
                    self.watch_path,
                    genepanel_dir
                )

                genepanel_name, genepanel_version = genepanel_dir.split('_', 1)

                if self.session.query(gene.Genepanel).filter(
                    gene.Genepanel.name == genepanel_name,
                    gene.Genepanel.version == genepanel_version
                ).count():
                    log.debug("Genepanel {} already imported.".format(genepanel_dir))
                    continue
                else:
                    log.info("Genepanel {} not in database, importing...".format(genepanel_dir))

                transcripts_path = os.path.join(genepanel_path, genepanel_dir + '.transcripts.csv')
                phenotypes_path = os.path.join(genepanel_path, genepanel_dir + '.phenotypes.csv')

                if not os.path.exists(transcripts_path):
                    raise RuntimeError("Missing transcripts file at {}".format(transcripts_path))

                if not os.path.exists(phenotypes_path):
                    log.warning("Missing phenotypes file. Phenotypes will not be imported!")
                    phenotypes_path = None

                self.import_genepanel(
                    transcripts_path,
                    phenotypes_path,
                    genepanel_name,
                    genepanel_version
                )

                # All is apparantly good, let's commit!
                self.session.commit()
                log.info("Genepanel {} imported successfully!".format(genepanel_dir))

            # Catch all exceptions and carry on, otherwise one bad analysis can block all of them
            except Exception:
                log.exception("An exception occured while import a new genepanel. Skipping...")
                self.session.rollback()
