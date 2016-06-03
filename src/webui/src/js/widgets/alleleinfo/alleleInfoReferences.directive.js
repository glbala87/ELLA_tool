/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-references',
    templateUrl: 'ngtmpl/alleleInfoReferences.ngtmpl.html',
    scope: {
        analysis: '=',
        allele: '=',
        references: '=',
        alleleState: '=',
        onSave: '&?'
    }
})
@Inject('$scope', 'ReferenceEvalModal', 'Interpretation')
export class AlleleInfoReferences {
    constructor($scope, ReferenceEvalModal, Interpretation) {
        $scope.$watchCollection(
            () => this.references,
            () => this.allele_references = this.getReferences()
        );
        this.refEvalModal = ReferenceEvalModal;
        this.interpretationService = Interpretation;
    }

    /**
     * Retrives combined PubMed IDs for all alles.
     * @return {Array} Array of ids.
     */
    _getPubmedIds(alleles) {
        let ids = [];
        for (let allele of alleles) {
            Array.prototype.push.apply(ids, allele.getPubmedIds());
        }
        return ids;
    }


    /**
     * Returns a list of references for this.allele
     * @return {Array} List of [Reference, ...].
     */
    getReferences() {
        let references = [];
        if (this.references) {
            for (let pmid of this.allele.getPubmedIds()) {
                let reference = this.references.find(r => r.pubmedID === pmid);
                if (reference) {
                    references.push(reference);
                }
            }
        }
        return references;
    }

    _getExistingReferenceAssessment(reference) {
        if (this.allele.reference_assessments) {
            return this.allele.reference_assessments.find(ra => {
                return ra.reference_id === reference.id;
            });
        }
    }

    getCurrentReferenceAssessment(reference) {
        if (!('referenceassessments' in this.alleleState)) {
            this.alleleState.referenceassessments = [];
        }

        let refassessment = this.alleleState.referenceassessments.find(
            ra => ra.allele_id === this.allele.id &&
                  ra.reference_id === reference.id
        );
        if (!refassessment) {
            refassessment = {
                allele_id: this.allele.id,
                reference_id: reference.id
            };

            // If it has existing reference_assessment, user is now going to edit it
            // Copy it into the state since all changes user does
            // happens on the interpretation state.
            let existing = this._getExistingReferenceAssessment(reference)
            if (existing) {
                Object.assign(refassessment, JSON.parse(JSON.stringify(existing)));
                refassessment.id = existing.id;
            }
            this.alleleState.referenceassessments.push(refassessment);
        }
        return refassessment;
    }

    showReferenceEval(reference) {
        this.refEvalModal.show(
            this.analysis,
            this.allele,
            reference,
            this.getCurrentReferenceAssessment(reference)
        ).then((ra) => {
            if (ra) {
                let state_ra = this.getCurrentReferenceAssessment(reference);
                state_ra.evaluation = ra.evaluation;
                delete state_ra.id;  // Remove 'id' in case it was an existing assessment that's been modified
                if (this.onSave) {
                    this.onSave();
                }
            }
        });

    }
}
