#!/usr/bin/env python

"""
Exports all pubmed ids present in annotation in the database
by running the annotation rows through AnnotationProcessor.
"""

from api.util.annotationprocessor import AnnotationProcessor
from vardb.datamodel import DB, annotation


db = DB()
db.connect()
session = db.session

annotations = session.query(annotation.Annotation).all()
pubmeds = list()
for a in annotations:
    pubmeds += [r['pubmed_id'] for r in AnnotationProcessor.process(a.annotations)['references']]


for pmid in list(set(pubmeds)):
    print pmid
