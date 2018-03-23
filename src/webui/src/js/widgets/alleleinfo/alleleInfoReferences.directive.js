/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'
import { AlleleStateHelper } from '../../model/allelestatehelper'
import { deepCopy } from '../../util'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, string, signal } from 'cerebral/tags'
import getReferenceAnnotation from '../../store/modules/views/workflows/interpretation/computed/getReferenceAnnotation'

app.component('alleleInfoReferences', {
    bindings: {
        title: '@',
        type: '@'
    },
    templateUrl: 'ngtmpl/alleleInfoReferences-new.ngtmpl.html',
    controller: connect(
        {
            references: getReferenceAnnotation(
                props`type`,
                state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
                state`views.workflows.interpretation.selected`,
                state`views.workflows.data.references`
            ),
            showExcluded: state`views.workflows.interpretation.selected.user_state.allele.${state`views.workflows.selectedAllele`}.showExcludedReferences`
        },
        'AlleleInfoReferences',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    hasContent() {
                        if ($ctrl.references) {
                            return (
                                $ctrl.references[$ctrl.type].unpublished.length +
                                    $ctrl.references[$ctrl.type].published.length >
                                0
                            )
                        }
                        return false
                    }
                })
            }
        ]
    )
})

@Directive({
    selector: 'allele-info-references-old',
    templateUrl: 'ngtmpl/alleleInfoReferences.ngtmpl.html',
    scope: {
        analysis: '=',
        allele: '=',
        references: '=',
        alleleState: '=',
        alleleUserState: '=',
        onSave: '&?',
        readOnly: '=?',
        title: '@'
    }
})
@Inject('$scope', 'ReferenceEvalModal')
export class AlleleInfoReferences {
    constructor($scope, ReferenceEvalModal) {
        this.refEvalModal = ReferenceEvalModal

        this.refViewType = this.title
        this.allele_references = []
        // If we have PMID in annotation,
        // but not the reference in the database.
        // Used in order to ask the user to add it manually.
        this.missing_references = []

        $scope.$watchCollection(
            () => this.references,
            () => {
                if (this.allele && this.references) {
                    this.setAlleleReferences()
                }
            }
        )
        $scope.$watch(
            () => this.allele,
            () => {
                if (this.allele && this.references) {
                    this.setAlleleReferences()
                }
            }
        )
    }

    setAlleleReferences() {
        this.allele_references = []
        this.missing_references = []

        for (let ids of this.allele.getReferenceIds()) {
            let pmid = ids.pubmed_id
            let id = ids.id

            let reference_found = false
            if (this.references) {
                if (pmid) {
                    var reference = this.references.find(r => r.pubmed_id === pmid)
                } else {
                    var reference = this.references.find(r => r.id === id)
                }

                if (reference) {
                    this.allele_references.push(reference)
                    reference_found = true
                }
            }
            if (!reference_found) {
                this.missing_references.push(ids)
            }
        }
    }

    getPendingReferences(published) {
        if (this.refViewType === 'Pending') {
            return this.allele_references.filter(
                r =>
                    r.published === published &&
                    this.hasReferenceAssessment(r) === false &&
                    ['Ignore', 'No'].indexOf(this.getReferenceAssessment(r).evaluation.relevance) <
                        0
            )
        } else return []
    }

    getEvaluatedReferences(published) {
        if (this.refViewType === 'Evaluated') {
            return this.allele_references.filter(
                r =>
                    this.isIgnored(r) === false &&
                    r.published === published &&
                    this.hasReferenceAssessment(r) === true
            )
        } else return []
    }

    getExcludedReferences(published) {
        if (this.refViewType === 'Excluded') {
            return this.allele_references.filter(
                r => this.isIgnored(r) === true && r.published === published
            )
        } else return []
    }

    isIgnored(reference) {
        let refAssess = this.getReferenceAssessment(reference)
        let result = ['Ignore', 'No'].indexOf(refAssess.evaluation.relevance) >= 0
        return result
    }

    hasReferences() {
        if (this.refViewType === 'Pending') {
            return (
                this.missing_references.length +
                this.getPendingReferences(true).length +
                this.getPendingReferences(false).length
            )
        } else if (this.refViewType === 'Evaluated') {
            return (
                this.getEvaluatedReferences(true).length + this.getEvaluatedReferences(false).length
            )
        } else {
            if (this.alleleUserState.showExcludedReferences) {
                return (
                    this.getExcludedReferences(true).length +
                    this.getExcludedReferences(false).length
                )
            } else -1
        }
    }

    getReferencesIgnored() {
        return this.allele_references.filter(
            ref =>
                ['Ignore', 'No'].indexOf(this.getReferenceAssessment(ref).evaluation.relevance) >= 0
        )
    }

    getReferenceAssessment(reference) {
        return AlleleStateHelper.getReferenceAssessment(this.allele, reference, this.alleleState)
    }

    hasReferenceAssessment(reference) {
        return AlleleStateHelper.hasReferenceAssessment(this.allele, reference, this.alleleState)
    }

    getReferencesWithoutAssessment() {
        return this.allele_references.filter(ref => !this.hasReferenceAssessment(ref))
    }

    _refHasRelevantAssessment = ref => {
        return (
            this.hasReferenceAssessment(ref) &&
            ['Ignore', 'No'].indexOf(this.getReferenceAssessment(ref).evaluation.relevance) < 0
        )
    }

    getReferencesWithAssessment() {
        return this.allele_references.filter(ref => this._refHasRelevantAssessment(ref))
    }

    existsReferenceAssesment() {
        return this.allele_references.find(ref => this._refHasRelevantAssessment(ref))
    }

    getEvaluateBtnText(reference) {
        if (this.readOnly) {
            return 'See details'
        }

        if (this.hasReferenceAssessment(reference)) {
            return 'Re-evaluate'
        }
        return 'Evaluate'
    }

    quickIgnore(reference) {
        let referenceAssessment = deepCopy(this.getReferenceAssessment(reference))

        referenceAssessment.evaluation = { relevance: 'Ignore' }
        AlleleStateHelper.updateReferenceAssessment(
            this.allele,
            reference,
            this.alleleState,
            referenceAssessment
        )
        if (this.onSave) {
            this.onSave()
        }
    }

    showReferenceEval(reference) {
        // Check for existing referenceassessment data (either from existing ra from backend
        // or user data in the allele state)
        let existing_ra = AlleleStateHelper.getReferenceAssessment(
            this.allele,
            reference,
            this.alleleState
        )

        this.refEvalModal
            .show(this.analysis, this.allele, reference, existing_ra, this.readOnly)
            .then(dialogResult => {
                // If dialogResult is an object, then the referenceassessment
                // was changed and we should replace it in our state.
                // If modal was canceled or no changes took place, it's 'undefined'.
                if (this.readOnly) {
                    // don't save anything
                    return
                }
                if (dialogResult) {
                    AlleleStateHelper.updateReferenceAssessment(
                        this.allele,
                        reference,
                        this.alleleState,
                        dialogResult
                    )
                    if (this.onSave) {
                        this.onSave()
                    }
                }
            })
    }
}
