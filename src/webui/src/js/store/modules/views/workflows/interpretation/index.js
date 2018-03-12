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
import ignoreReferenceClicked from './signals/ignoreReferenceClicked'
import removeAcmgClicked from './signals/removeAcmgClicked'
import reviewCommentChanged from './signals/reviewCommentChanged'
import interpretationUserStateChanged from './signals/interpretationUserStateChanged'
import upgradeDowngradeAcmgClicked from './signals/upgradeDowngradeAcmgClicked'

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
        ignoreReferenceClicked,
        alleleReportCommentChanged,
        reportCommentChanged,
        removeAcmgClicked,
        reviewCommentChanged,
        reuseAlleleAssessmentClicked,
        interpretationUserStateChanged,
        upgradeDowngradeAcmgClicked
    }
})
