import { Module } from 'cerebral'
import addAcmgClicked from './signals/addAcmgClicked'
import addCustomAnnotationClicked from './signals/addCustomAnnotationClicked'
import evaluateReferenceClicked from './signals/evaluateReferenceClicked'
import collapseAlleleSectionboxChanged from './signals/collapseAlleleSectionboxChanged'
import collapseAllAlleleSectionboxClicked from './signals/collapseAllAlleleSectionboxChangedClicked'
import acmgCodeChanged from './signals/acmgCodeChanged'
import reuseAlleleAssessmentClicked from './signals/reuseAlleleAssessmentClicked'
import alleleReportCommentChanged from './signals/alleleReportCommentChanged'
import reportCommentChanged from './signals/reportCommentChanged'
import evaluationCommentChanged from './signals/evaluationCommentChanged'
import classificationChanged from './signals/classificationChanged'
import analysisCommentChanged from './signals/analysisCommentChanged'
import ignoreReferenceClicked from './signals/ignoreReferenceClicked'
import removeAcmgClicked from './signals/removeAcmgClicked'
import removeAttachmentClicked from './signals/removeAttachmentClicked'
import showExcludedReferencesClicked from './signals/showExcludedReferencesClicked'
import showAlleleAssessmentHistoryClicked from './signals/showAlleleAssessmentHistoryClicked'
import interpretationUserStateChanged from './signals/interpretationUserStateChanged'
import upgradeDowngradeAcmgClicked from './signals/upgradeDowngradeAcmgClicked'
import uploadAttachmentTriggered from './signals/uploadAttachmentTriggered'

export default Module({
    state: {},
    signals: {
        addAcmgClicked,
        addCustomAnnotationClicked,
        evaluateReferenceClicked,
        collapseAllAlleleSectionboxClicked,
        collapseAlleleSectionboxChanged,
        acmgCodeChanged,
        classificationChanged,
        evaluationCommentChanged,
        analysisCommentChanged,
        ignoreReferenceClicked,
        alleleReportCommentChanged,
        reportCommentChanged,
        removeAcmgClicked,
        removeAttachmentClicked,
        reuseAlleleAssessmentClicked,
        interpretationUserStateChanged,
        showExcludedReferencesClicked,
        showAlleleAssessmentHistoryClicked,
        upgradeDowngradeAcmgClicked,
        uploadAttachmentTriggered
    }
})
