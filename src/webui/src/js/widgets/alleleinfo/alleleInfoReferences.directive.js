/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {AlleleStateHelper} from '../../model/allelestatehelper';
import {deepCopy} from '../../util';


@Directive({
    selector: 'allele-info-references',
    templateUrl: 'ngtmpl/alleleInfoReferences.ngtmpl.html',
    scope: {
        analysis: '=',
        allele: '=',
        references: '=',
        alleleState: '=',
        alleleUserState: '=',
        onSave: '&?',
        readOnly: '=?'
    }
})
@Inject('$scope', 'ReferenceEvalModal')
export class AlleleInfoReferences {
    constructor($scope, ReferenceEvalModal) {


        this.allele_references = [];
        // If we have PMID in annotation,
        // but not the reference in the database.
        // Used in order to ask the user to add it manually.
        this.missing_references = [];
        $scope.$watchCollection(
            () => this.references,
            () => {
                if (this.allele && this.references) {
                    this.setAlleleReferences();
                }
            }

        );
        $scope.$watch(
            () => this.allele,
            () => {
                if (this.allele && this.references) {
                    this.setAlleleReferences();
                }
            }
        );
        this.refEvalModal = ReferenceEvalModal;
    }

    getPubmedUrl(pmid) {
        return `http://www.ncbi.nlm.nih.gov/pubmed/${pmid}`;
    }

    setAlleleReferences() {
        this.allele_references = [];
        this.missing_references = [];

        for (let ids of this.allele.getReferenceIds()) {
            let pmid = ids.pubmed_id;
            let id = ids.id;
            let reference_found = false;
            if (this.references) {
                if (pmid !== undefined) {
                    var reference = this.references.find(r => r.pubmed_id === pmid);
                } else {
                    var reference = this.references.find(r => r.id === id);
                }

                if (reference) {
                    this.allele_references.push(reference);
                    reference_found = true;
                }
            }
            if (!reference_found) {
                this.missing_references.push(ids);
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
        return AlleleStateHelper.hasReferenceAssessment(
            this.allele,
            reference,
            this.alleleState
        );

    }

    getEvaluateBtnText(reference) {
        if (this.readOnly) {
            return 'See details'
        }

        if (this.hasReferenceAssessment(reference)) {
            return 'Re-evaluate';
        }
        return 'Evaluate';
    }

    quickIgnore(reference) {
        let referenceAssessment = deepCopy(this.getReferenceAssessment(reference));

        referenceAssessment.evaluation = {relevance: "Ignore"};
        AlleleStateHelper.updateReferenceAssessment(
            this.allele,
            reference,
            this.alleleState,
            referenceAssessment
        );
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
        );
        this.refEvalModal.show(
            this.analysis,
            this.allele,
            reference,
            existing_ra,
            this.readOnly
        ).then(dialogResult => {
            // If dialogResult is an object, then the referenceassessment
            // was changed and we should replace it in our state.
            // If modal was canceled or no changes took place, it's 'undefined'.
            if (this.readOnly) { // don't save anything
                return;
            }
            if (dialogResult) {
                AlleleStateHelper.updateReferenceAssessment(
                    this.allele,
                    reference,
                    this.alleleState,
                    dialogResult
                );
                if (this.onSave) {
                    this.onSave();
                }
            }
        });

    }
}
