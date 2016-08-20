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
        this.allele_references = [];
        // If we have PMID in annotation,
        // but not the reference in the database.
        // Used in order to ask the user to add it manually.
        this.missing_references = [];
        $scope.$watchCollection(
            () => this.references,
            () => this.setAlleleReferences()
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

    getPubmedUrl(pmid) {
        return `http://www.ncbi.nlm.nih.gov/pubmed/${pmid}`;
    }

    /**
     * Returns a list of references for this.allele
     * @return {Array} List of [Reference, ...].
     */
    setAlleleReferences() {
        this.allele_references = [];
        this.missing_references = [];
        for (let pmid of this.allele.getPubmedIds()) {
            let reference_found = false;
            if (this.references) {
                let reference = this.references.find(r => r.pubmed_id === pmid);
                if (reference) {
                    this.allele_references.push(reference);
                    reference_found = true;
                }
            }
            if (!reference_found) {
                this.missing_references.push(pmid);
            }
        }
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

    getEvaluateBtnText(reference) {
        if (this._getExistingReferenceAssessment(reference)) {
            return 'Reevaluate';
        }
        return 'Evaluate';
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
