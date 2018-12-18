#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""Code for testing gene, transcript, genepanel datamodel.

See howToTestDB.py for explanation/comments on how to create tests with SQLAlchemy.
Remember to CREATE DATABASE testvardb; before running this code.
"""

import sys
import unittest
import operator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import BinaryExpression as BE
from sqlalchemy.exc import IntegrityError

from vardb.datamodel import Base  # Must use same Base as tested modules
from vardb.datamodel import gene

if sys.platform.startswith("win"):
    Engine = create_engine("postgresql+psycopg2://postgres@localhost/testvardb")
else:
    Engine = create_engine("postgresql+psycopg2://localhost/testvardb")

Session = sessionmaker()
Base.metadata.drop_all(Engine)
Base.metadata.create_all(Engine)


class TestGene(unittest.TestCase):
    """Test Gene class"""

    def setUp(self):
        self.connection = Engine.connect()
        self.trans = self.connection.begin()
        self.session = Session(bind=self.connection)

    def tearDown(self):
        self.trans.rollback()
        self.session.close()
        self.connection.close()  # Return connection to the Engine

    def test_add_gene(self):
        g = gene.Gene.create_or_update_gene(self.session, "BRCA1", "ENSG00000012048", "Dom")

        genesInDB = self.session.query(gene.Gene).all()
        self.assertEqual(len(genesInDB), 1)
        self.assertEqual(genesInDB[0].hugoSymbol, "BRCA1")
        self.assertEqual(genesInDB[0].dominance, g.dominance)

    def test_adding_gene_that_already_exists_updates_it(self):
        g = gene.Gene.create_or_update_gene(self.session, "BRCA1", "ENSG00000012048", "Dom")
        self.session.commit()
        g2 = gene.Gene.create_or_update_gene(self.session, "BRCA1", "ENSG00000012048", "Res")
        self.session.commit()
        self.assertEqual(g, g2)
        self.assertEqual(g.dominance, "Res")


class TestTranscript(unittest.TestCase):
    """Test Transcript class"""

    def setUp(self):
        self.connection = Engine.connect()
        self.trans = self.connection.begin()
        self.session = Session(bind=self.connection)
        self.g1 = gene.Gene.create_or_update_gene(self.session, "BRCA1", "ENSG00000012048", "Dom")

    def tearDown(self):
        self.trans.rollback()
        self.session.close()
        self.connection.close()

    # def test_add_transcript(self):
    #     t = gene.Transcript.create_or_update_transcript(self.session, self.g1, "NM_123", "ENST1", "GRCh37", "1", 100, 200, '+',
    #                             105, 166, [105, 140, 160], [110, 150, 175])
    #     t2 = gene.Transcript.create_or_update_transcript(self.session, self.g1, "NM_987", "ENST2", "GRCh37", "X", 100, 200, '+',
    #                             105, 166, [105, 140, 160], [110, 150, 175])
    #     tInDB = self.session.query(gene.Transcript).all()
    #     self.assertEqual(len(tInDB), 2)
    #     tInDB = self.session.query(gene.Transcript).filter(gene.Transcript.refseqName=="NM_123").all()
    #     self.assertEqual(tInDB[0].refseqName, "NM_123")


class TestGenepanel(unittest.TestCase):
    """Test Genepanel class"""

    def setUp(self):
        self.connection = Engine.connect()
        self.trans = self.connection.begin()
        self.session = Session(bind=self.connection)
        self.g1 = gene.Gene("BRCA1", "ENS123", "dom")
        self.transcripts = []
        self.transcripts.append(
            gene.Transcript(
                self.g1,
                "NM_123",
                "ENST1",
                "GRCh37",
                "1",
                100,
                200,
                "+",
                105,
                166,
                [105, 140, 160],
                [110, 150, 175],
            )
        )

    def tearDown(self):
        self.trans.rollback()
        self.session.close()
        self.connection.close()


if __name__ == "__main__":
    unittest.main(exit=False)
