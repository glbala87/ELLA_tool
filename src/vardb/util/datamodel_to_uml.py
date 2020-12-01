import tempfile
import os
import sadisplay
from vardb.datamodel import allele, sample, genotype
from vardb.datamodel import annotation, assessment, annotationshadow
from vardb.datamodel import gene, workflow, user, attachment, log

GROUPS = [
    {
        "name": "all",
        "tables": [
            allele.Allele,
            attachment.Attachment,
            assessment.AlleleAssessment,
            assessment.AlleleAssessment,
            assessment.AlleleAssessmentAttachment,
            assessment.AlleleReport,
            assessment.ReferenceAssessment,
            sample.Sample,
            sample.Analysis,
            sample.FilterConfig,
            sample.UserGroupFilterConfig,
            workflow.AlleleInterpretation,
            workflow.AnalysisInterpretation,
            workflow.AlleleInterpretationSnapshot,
            workflow.AnalysisInterpretationSnapshot,
            workflow.InterpretationLog,
            genotype.Genotype,
            genotype.GenotypeSampleData,
            gene.Gene,
            gene.Genepanel,
            annotation.Annotation,
            annotation.CustomAnnotation,
            gene.Transcript,
            gene.Phenotype,
            gene.genepanel_transcript,
            gene.genepanel_phenotype,
            user.User,
            user.UserGroup,
            user.UserGroupGenepanel,
            user.UserSession,
            user.UserOldPassword,
            annotationshadow.AnnotationShadowFrequency,
            annotationshadow.AnnotationShadowTranscript,
            log.CliLog,
            log.ResourceLog,
        ],
    },
    {
        "name": "analysis",
        "tables": [
            allele.Allele,
            sample.Sample,
            sample.Analysis,
            genotype.Genotype,
            genotype.GenotypeSampleData,
            annotation.Annotation,
        ],
    },
    {
        "name": "workflow",
        "tables": [
            allele.Allele,
            sample.Analysis,
            workflow.AlleleInterpretation,
            workflow.AnalysisInterpretation,
            workflow.AlleleInterpretationSnapshot,
            workflow.AnalysisInterpretationSnapshot,
            workflow.InterpretationLog,
        ],
    },
    {
        "name": "evaluation",
        "tables": [
            allele.Allele,
            attachment.Attachment,
            assessment.AlleleAssessment,
            assessment.AlleleAssessmentAttachment,
            assessment.AlleleReport,
            assessment.ReferenceAssessment,
        ],
    },
    {
        "name": "user",
        "tables": [
            user.User,
            user.UserGroup,
            user.UserGroupGenepanel,
            user.UserSession,
            user.UserOldPassword,
            sample.FilterConfig,
            sample.UserGroupFilterConfig,
        ],
    },
    {
        "name": "genepanel",
        "tables": [
            gene.Transcript,
            gene.Phenotype,
            gene.genepanel_transcript,
            gene.genepanel_phenotype,
            user.UserGroupGenepanel,
            gene.Gene,
            gene.Genepanel,
        ],
    },
    {
        "name": "annotation",
        "tables": [
            allele.Allele,
            annotation.Annotation,
            annotation.CustomAnnotation,
            annotationshadow.AnnotationShadowFrequency,
            annotationshadow.AnnotationShadowTranscript,
        ],
    },
    {"name": "log", "tables": [user.UserSession, log.ResourceLog, log.CliLog]},
]

print("Generating diagrams...")
for group in GROUPS:
    desc = sadisplay.describe(group["tables"])
    name = f"ella-datamodel-{group['name']}"
    with tempfile.NamedTemporaryFile() as f:
        f.write(sadisplay.dot(desc).encode())
        print(f"Writing {name}.png")
        os.system(f"dot -Tpng {f.name} > {name}.png")
print("Done!")
