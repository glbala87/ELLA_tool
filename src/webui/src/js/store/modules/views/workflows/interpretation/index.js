import { Module } from 'cerebral'
import addAcmgClicked from './signals/addAcmgClicked'
import geneAssessmentChanged from './signals/geneAssessmentChanged'
import undoGeneAssessmentClicked from './signals/undoGeneAssessmentClicked'
import updateGeneAssessmentClicked from './signals/updateGeneAssessmentClicked'
import referenceAssessmentCommentChanged from './signals/referenceAssessmentCommentChanged'
import collapseAlleleSectionboxChanged from './signals/collapseAlleleSectionboxChanged'
import collapseAllAlleleSectionboxClicked from './signals/collapseAllAlleleSectionboxChangedClicked'
import acmgCodeChanged from './signals/acmgCodeChanged'
import finalizeAlleleClicked from './signals/finalizeAlleleClicked'
import reuseAlleleAssessmentClicked from './signals/reuseAlleleAssessmentClicked'
import alleleReportCommentChanged from './signals/alleleReportCommentChanged'
import reportCommentChanged from './signals/reportCommentChanged'
import evaluationCommentChanged from './signals/evaluationCommentChanged'
import classificationChanged from './signals/classificationChanged'
import analysisCommentChanged from './signals/analysisCommentChanged'
import ignoreReferenceClicked from './signals/ignoreReferenceClicked'
import reuseAlleleReportClicked from './signals/reuseAlleleReportClicked'
import removeAcmgClicked from './signals/removeAcmgClicked'
import removeAttachmentClicked from './signals/removeAttachmentClicked'
import showExcludedReferencesClicked from './signals/showExcludedReferencesClicked'
import interpretationUserStateChanged from './signals/interpretationUserStateChanged'
import upgradeDowngradeAcmgClicked from './signals/upgradeDowngradeAcmgClicked'
import uploadAttachmentTriggered from './signals/uploadAttachmentTriggered'
import indicationsCommentChanged from './signals/indicationsCommentChanged'

export default Module({
    state: {},
    signals: {
        addAcmgClicked,
        geneAssessmentChanged,
        undoGeneAssessmentClicked,
        updateGeneAssessmentClicked,
        referenceAssessmentCommentChanged,
        collapseAllAlleleSectionboxClicked,
        collapseAlleleSectionboxChanged,
        acmgCodeChanged,
        finalizeAlleleClicked,
        classificationChanged,
        evaluationCommentChanged,
        analysisCommentChanged,
        ignoreReferenceClicked,
        alleleReportCommentChanged,
        reportCommentChanged,
        reuseAlleleReportClicked,
        removeAcmgClicked,
        removeAttachmentClicked,
        reuseAlleleAssessmentClicked,
        interpretationUserStateChanged,
        showExcludedReferencesClicked,
        upgradeDowngradeAcmgClicked,
        uploadAttachmentTriggered,
        indicationsCommentChanged
    }
})
