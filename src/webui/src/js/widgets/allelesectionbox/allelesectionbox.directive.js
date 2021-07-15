import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal, props } from 'cerebral/tags'
import { Compute } from 'cerebral'

import isAlleleAssessmentOutdated from '../../store/common/computes/isAlleleAssessmentOutdated'
import hasExistingAlleleAssessment from '../../store/common/computes/hasExistingAlleleAssessment'
import isAlleleAssessmentReused from '../../store/modules/views/workflows/interpretation/computed/isAlleleAssessmentReused'
import getAlleleAssessment from '../../store/modules/views/workflows/interpretation/computed/getAlleleAssessment'
import getAlleleReport from '../../store/modules/views/workflows/interpretation/computed/getAlleleReport'
import hasExistingAlleleReport from '../../store/common/computes/hasExistingAlleleReport'
import isAlleleReportUpdated from '../../store/modules/views/workflows/interpretation/computed/isAlleleReportUpdated'
import getVerificationStatus from '../../store/modules/views/workflows/interpretation/computed/getVerificationStatus'
import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import getReferenceAssessment from '../../store/modules/views/workflows/interpretation/computed/getReferenceAssessment'
import {
    getReferencesIdsForAllele,
    findReferencesFromIds,
    isIgnored
} from '../../store/common/helpers/reference'
import { deepCopy } from '../../util'
import getAlleleState from '../../store/modules/views/workflows/interpretation/computed/getAlleleState'
import getNotRelevant from '../../store/modules/views/workflows/interpretation/computed/getNotRelevant'
import template from './allelesectionbox.ngtmpl.html' // eslint-disable-line no-unused-vars
import getEditorReferences from '../../store/modules/views/workflows/interpretation/computed/getEditorReferences'
import canFinalizeAllele from '../../store/modules/views/workflows/computed/canFinalizeAllele'
import { sortCodesByTypeStrength } from '../../store/common/helpers/acmg'

const getExcludedReferencesCount = Compute(
    state`views.workflows.interpretation.data.alleles.${state`views.workflows.selectedAllele`}`,
    state`views.workflows.interpretation.data.references`,
    (allele, references, get) => {
        if (!allele || !references) {
            return
        }
        const alleleReferenceIds = getReferencesIdsForAllele(allele)
        const alleleReferences = findReferencesFromIds(
            Object.values(references),
            alleleReferenceIds
        ).references
        return alleleReferences
            .map((r) => get(getReferenceAssessment(allele.id, r.id)) || null)
            .filter((ra) => {
                return isIgnored(ra)
            }).length
    }
)

const getSection = Compute(
    state`views.workflows.selectedComponent`,
    state`views.workflows.components`,
    props`sectionKey`,
    (selectedComponent, components, sectionKey) => {
        if (!selectedComponent) {
            return
        }
        if (selectedComponent in components && components[selectedComponent].sections) {
            return components[selectedComponent].sections[sectionKey]
        }
    }
)

const getSectionBoxContents = Compute(
    state`views.workflows.selectedComponent`,
    state`views.workflows.components`,
    state`views.workflows.selectedAllele`,
    props`sectionKey`,
    (selectedComponent, components, selectedAllele, sectionKey) => {
        if (!selectedComponent) {
            return []
        }
        if (selectedComponent in components && components[selectedComponent].sectionContent) {
            return components[selectedComponent].sectionContent[selectedAllele][sectionKey]
        } else {
            return []
        }
    }
)

const isCollapsed = Compute(
    state`views.workflows.interpretation.userState`,
    state`views.workflows.selectedAllele`,
    props`sectionKey`,
    (userState, selectedAllele, sectionKey) => {
        const COLLAPSED_BY_DEFAULT = []
        if (!userState || !userState.allele) {
            return
        }
        if (
            selectedAllele in userState.allele &&
            'sections' in userState.allele[selectedAllele] &&
            sectionKey in userState.allele[selectedAllele].sections
        ) {
            return userState.allele[selectedAllele].sections[sectionKey].collapsed
        }
        return COLLAPSED_BY_DEFAULT.includes(sectionKey)
    }
)

const classificationOptions = Compute(state`app.config`, (config) => {
    return [{ name: 'Select class', value: null }].concat(config.classification.options)
})

app.component('alleleSectionbox', {
    bindings: {
        sectionKey: '<'
    },
    templateUrl: 'allelesectionbox.ngtmpl.html',
    controller: connect(
        {
            classificationOptions,
            collapsed: isCollapsed,
            readOnly: isReadOnly,
            section: getSection,
            sectionBoxContents: getSectionBoxContents,
            config: state`app.config`,
            canFinalizeSelectedAllele: canFinalizeAllele(state`views.workflows.selectedAllele`),
            commentTemplates: state`app.commentTemplates`,
            selectedAllele: state`views.workflows.selectedAllele`,
            alleleState: getAlleleState(state`views.workflows.selectedAllele`),
            alleleassessment: getAlleleAssessment(state`views.workflows.selectedAllele`),
            allelereport: getAlleleReport(state`views.workflows.selectedAllele`),
            editorReferences: getEditorReferences(),
            isAlleleAssessmentOutdated: isAlleleAssessmentOutdated(
                state`views.workflows.interpretation.data.alleles.${state`views.workflows.selectedAllele`}`
            ),
            hasExistingAlleleAssessment: hasExistingAlleleAssessment(
                state`views.workflows.interpretation.data.alleles.${state`views.workflows.selectedAllele`}`
            ),
            isAlleleAssessmentReused: isAlleleAssessmentReused(
                state`views.workflows.selectedAllele`
            ),
            hasExistingAlleleReport: hasExistingAlleleReport(
                state`views.workflows.interpretation.data.alleles.${state`views.workflows.selectedAllele`}`
            ),
            isAlleleReportUpdated: isAlleleReportUpdated(state`views.workflows.selectedAllele`),
            showExcludedReferences: state`views.workflows.interpretation.userState.allele.${state`views.workflows.selectedAllele`}.showExcludedReferences`,
            verificationStatus: getVerificationStatus(state`views.workflows.selectedAllele`),
            notRelevant: getNotRelevant(state`views.workflows.selectedAllele`),
            verificationStatusChanged: signal`views.workflows.verificationStatusChanged`,
            notRelevantChanged: signal`views.workflows.notRelevantChanged`,
            finalizeAlleleClicked: signal`views.workflows.interpretation.finalizeAlleleClicked`,
            addPredictionClicked: signal`views.workflows.modals.addPrediction.showAddPredictionClicked`,
            addExternalClicked: signal`views.workflows.modals.addExternal.showAddExternalClicked`,
            addReferencesClicked: signal`views.workflows.modals.addReferences.showAddReferencesClicked`,
            classificationChanged: signal`views.workflows.interpretation.classificationChanged`,
            collapseAlleleSectionboxChanged: signal`views.workflows.interpretation.collapseAlleleSectionboxChanged`,
            evaluationCommentChanged: signal`views.workflows.interpretation.evaluationCommentChanged`,
            alleleReportCommentChanged: signal`views.workflows.interpretation.alleleReportCommentChanged`,
            analysisCommentChanged: signal`views.workflows.interpretation.analysisCommentChanged`,
            reuseAlleleAssessmentClicked: signal`views.workflows.interpretation.reuseAlleleAssessmentClicked`,
            reuseAlleleReportClicked: signal`views.workflows.interpretation.reuseAlleleReportClicked`,
            removeAcmgClicked: signal`views.workflows.interpretation.removeAcmgClicked`,
            acmgCodeChanged: signal`views.workflows.interpretation.acmgCodeChanged`,
            showExcludedReferencesClicked: signal`views.workflows.interpretation.showExcludedReferencesClicked`,
            excludedReferenceCount: getExcludedReferencesCount
        },
        'AlleleSectionbox',
        [
            '$scope',
            'cerebral',
            function($scope, cerebral) {
                const $ctrl = $scope.$ctrl

                // HACK: The <acmg> directive modifies the code object directly (which comes from Cerebral store),
                // which messes up handling in Cerebral
                // Until <acmg> is converted, we make local deep copies
                $scope.$watch(
                    () => {
                        return $ctrl.alleleassessment && $ctrl.alleleassessment.evaluation.acmg
                            ? $ctrl.alleleassessment.evaluation.acmg.included
                            : []
                    },
                    (items) => {
                        if (items) {
                            const includedAcmgCopies = items.map((i) => deepCopy(i))
                            // Order by pathogenicity and strength
                            const sortedIncludedAcmgCopies = sortCodesByTypeStrength(
                                includedAcmgCopies,
                                $ctrl.config
                            )
                            $ctrl.includedAcmgCopies = sortedIncludedAcmgCopies.pathogenic
                                .concat(sortedIncludedAcmgCopies.benign)
                                .concat(sortedIncludedAcmgCopies.other)
                        }
                    },
                    true
                )

                Object.assign($ctrl, {
                    showControls() {
                        if (
                            $ctrl.section.options &&
                            'hideControlsOnCollapse' in $ctrl.section.options
                        ) {
                            return !(
                                $ctrl.section.options.hideControlsOnCollapse && $ctrl.collapsed
                            )
                        }
                    },
                    collapseChangedWrapper(collapsed, section) {
                        $ctrl.collapseAlleleSectionboxChanged({
                            alleleId: $ctrl.selectedAllele,
                            collapsed,
                            section
                        })
                    },
                    getAllelePath() {
                        return `views.workflows.interpretation.data.alleles.${$ctrl.selectedAllele}`
                    },
                    getCardColor() {
                        if ($ctrl.section.alleleAssessmentReusedColor) {
                            return $ctrl.isAlleleAssessmentReused
                                ? $ctrl.section.alleleAssessmentReusedColor
                                : $ctrl.section.color
                        }
                        return $ctrl.section.color
                    },
                    acmgCodeChangedWrapper(code) {
                        $ctrl.acmgCodeChanged({ alleleId: $ctrl.selectedAllele, code })
                    },
                    getExcludedReferencesBtnText() {
                        return $ctrl.showExcludedReferences
                            ? `HIDE IGNORED (${$ctrl.excludedReferenceCount})`
                            : `SHOW IGNORED (${$ctrl.excludedReferenceCount})`
                    },
                    getAnalysisSpecificCommentTemplates() {
                        return $ctrl.commentTemplates['classificationAnalysisSpecific']
                    },
                    getAlleleassessmentCommentTemplates() {
                        const translations = {
                            classification: 'classificationEvaluation',
                            frequency: 'classificationFrequency',
                            external: 'classificationExternal',
                            prediction: 'classificationPrediction',
                            reference: 'classificationReferences'
                        }
                        const sectionName = $ctrl.section.alleleassessmentComment.name
                        return $ctrl.commentTemplates[translations[sectionName]]
                    },
                    getAlleleReportCommentTemplates() {
                        return $ctrl.commentTemplates['classificationReport']
                    },
                    getAcmgCommentTemplates() {
                        return $ctrl.commentTemplates['classificationAcmg']
                    },
                    reuseAlleleAssessment() {
                        $ctrl.reuseAlleleAssessmentClicked({ alleleId: $ctrl.selectedAllele })
                    },
                    reuseAlleleReport() {
                        $ctrl.reuseAlleleReportClicked({ alleleId: $ctrl.selectedAllele })
                    },
                    finalizeAllele() {
                        $ctrl.finalizeAlleleClicked({ alleleId: $ctrl.selectedAllele })
                    },
                    getFinalizeButtonText() {
                        // If only report will be updated, 'Submit report'.
                        // If both alleleassessment and report, 'Finalize'
                        if ($ctrl.isAlleleAssessmentReused) {
                            return 'Submit report'
                        }
                        return 'Finalize'
                    },
                    canFinalize() {
                        return Boolean(
                            $ctrl.canFinalizeSelectedAllele.canFinalize ||
                                ($ctrl.isAlleleAssessmentReused && $ctrl.isAlleleReportUpdated)
                        )
                    },
                    showFinalize() {
                        if ($ctrl.readOnly) {
                            return false
                        }
                        return $ctrl.isAlleleAssessmentReused ? $ctrl.isAlleleReportUpdated : true
                    },
                    finalizeTitle() {
                        if (!$ctrl.isAlleleAssessmentReused) {
                            return $ctrl.canFinalizeSelectedAllele.messages.join('\n')
                        }
                        return ''
                    }
                })
            }
        ]
    )
})
