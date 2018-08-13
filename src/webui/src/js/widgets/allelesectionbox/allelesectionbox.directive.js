import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal, props } from 'cerebral/tags'
import { Compute } from 'cerebral'

import isAlleleAssessmentOutdated from '../../store/common/computes/isAlleleAssessmentOutdated'
import hasExistingAlleleAssessment from '../../store/common/computes/hasExistingAlleleAssessment'
import isAlleleAssessmentReused from '../../store/modules/views/workflows/interpretation/computed/isAlleleAssessmentReused'
import getAlleleAssessment from '../../store/modules/views/workflows/interpretation/computed/getAlleleAssessment'
import getAlleleReport from '../../store/modules/views/workflows/interpretation/computed/getAlleleReport'
import getVerificationStatus from '../../store/modules/views/workflows/interpretation/computed/getVerificationStatus'
import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import getReferenceAssessment from '../../store/modules/views/workflows/interpretation/computed/getReferenceAssessment'
import {
    getReferencesIdsForAllele,
    findReferencesFromIds,
    isIgnored
} from '../../store/common/helpers/reference'
import { deepCopy } from '../../util'
import template from './allelesectionbox.ngtmpl.html'

const getExcludedReferencesCount = Compute(
    state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
    state`views.workflows.data.references`,
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

const isCollapsed = Compute(
    state`views.workflows.interpretation.selected.user_state`,
    state`views.workflows.selectedAllele`,
    props`sectionKey`,
    (userState, selectedAllele, sectionKey) => {
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
        return false
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
            selectedAllele: state`views.workflows.selectedAllele`,
            alleleassessment: getAlleleAssessment(state`views.workflows.selectedAllele`),
            allelereport: getAlleleReport(state`views.workflows.selectedAllele`),
            isAlleleAssessmentOutdated: isAlleleAssessmentOutdated(
                state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
            ),
            hasExistingAlleleAssessment: hasExistingAlleleAssessment(
                state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
            ),
            isAlleleAssessmentReused: isAlleleAssessmentReused(
                state`views.workflows.selectedAllele`
            ),
            showExcludedReferences: state`views.workflows.interpretation.selected.user_state.allele.${state`views.workflows.selectedAllele`}.showExcludedReferences`,
            verificationStatus: getVerificationStatus,
            verificationStatusChanged: signal`views.workflows.verificationStatusChanged`,
            addCustomAnnotationClicked: signal`views.workflows.interpretation.addCustomAnnotationClicked`,
            classificationChanged: signal`views.workflows.interpretation.classificationChanged`,
            collapseAlleleSectionboxChanged: signal`views.workflows.interpretation.collapseAlleleSectionboxChanged`,
            evaluationCommentChanged: signal`views.workflows.interpretation.evaluationCommentChanged`,
            alleleReportCommentChanged: signal`views.workflows.interpretation.alleleReportCommentChanged`,
            reuseAlleleAssessmentClicked: signal`views.workflows.interpretation.reuseAlleleAssessmentClicked`,
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
                            $ctrl.includedAcmgCopies = items.map((i) => deepCopy(i))
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
                        return `views.workflows.data.alleles.${$ctrl.selectedAllele}`
                    },
                    getCardColor() {
                        return $ctrl.isAlleleAssessmentReused ? 'green' : 'purple'
                    },
                    acmgCodeChangedWrapper(code) {
                        $ctrl.acmgCodeChanged({ alleleId: $ctrl.selectedAllele, code })
                    },
                    getExcludedReferencesBtnText() {
                        return $ctrl.showExcludedReferences
                            ? `HIDE IGNORED (${$ctrl.excludedReferenceCount})`
                            : `SHOW IGNORED (${$ctrl.excludedReferenceCount})`
                    }
                })
            }
        ]
    )
})
