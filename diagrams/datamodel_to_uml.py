import sadisplay
import os
from vardb.datamodel import allele, sample, genotype
from vardb.datamodel import annotation, assessment
from vardb.datamodel import gene, workflow, user

"""
Generating a diagram is a two step process:
- create a dot file (using python module sadispaly)
- create an image file from the dot file (using a program lik Graphviz that must must installed on your system)

"""

desc = sadisplay.describe(
    [
        allele.Allele,
        assessment.AlleleAssessment,
        assessment.ReferenceAssessment,
        sample.Sample,
        sample.Analysis,
        workflow.AlleleInterpretation,
        workflow.AnalysisInterpretation,
        workflow.AlleleInterpretationSnapshot,
        workflow.AnalysisInterpretationSnapshot,
        genotype.Genotype,
        gene.Gene,
        gene.Genepanel,
        annotation.Annotation,
        gene.Transcript,
        gene.Phenotype,
        user.User,
        user.UserGroup,
        user.UserGroupGenepanel,
        user.UserSession,
        user.UserOldPassword,
    ]
)
open("ella-datamodel.dot", "w").write(sadisplay.dot(desc))
