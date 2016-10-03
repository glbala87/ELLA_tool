/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {AlleleStateHelper} from '../../model/allelestatehelper';


@Directive({
    selector: 'allele-info-references',
    templateUrl: 'ngtmpl/alleleInfoReferences.ngtmpl.html',
    scope: {
        analysis: '=',
        allele: '=',
        references: '=',
        alleleState: '=',
        onSave: '&?',
        collapsed: '=?'
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
            () => {
                this.setAlleleReferences();
            }
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

    getReferenceAssessment(reference) {
        return AlleleStateHelper.getReferenceAssessment(
            this.allele,
            reference,
            this.alleleState
        );
    }

    hasReferenceAssessment(reference) {
        return AlleleStateHelper.getExistingReferenceAssessment(
            this.allele,
            reference,
            this.alleleState
        );
    }

    getEvaluateBtnText(reference) {
        if (this.hasReferenceAssessment(reference)) {
            return 'Re-evaluate';
        }
        return 'Evaluate';
    }

    showReferenceEval(reference) {
        // Check for existing referenceassessment data (either from existing ra from backend
        // or user data in the allele state)
        let existing_ra = AlleleStateHelper.getReferenceAssessment(
            this.allele,
            reference,
            this.alleleState
        );
        this.refEvalModal.show(
            this.analysis,
            this.allele,
            reference,
            existing_ra
        ).then(ra => {
            // If ra is an object, then the referenceassessment
            // was changed and we should replace it in our state.
            // If modal was canceled or no changes took place, it's 'undefined'.
            if (ra) {
                AlleleStateHelper.updateReferenceAssessment(
                    this.allele,
                    reference,
                    this.alleleState,
                    ra
                );
                if (this.onSave) {
                    this.onSave();
                }
            }
        });

    }
}
