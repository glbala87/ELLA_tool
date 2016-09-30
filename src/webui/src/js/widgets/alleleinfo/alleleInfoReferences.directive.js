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

    _createReferenceDBSources() {
        let referenceDBSources = {};
        for (let key in this.allele.annotation.references) {
            let ref = this.allele.annotation.references[key];
            referenceDBSources[ref.pubmed_id] = {};
            for (let sourceKey in ref.sources) {
                let source = ref.sources[sourceKey];
                let sourceStr = source;
                if (source in ref.sourceInfo) {
                    sourceStr += " ("+ref.sourceInfo[source]+")";
                }
                referenceDBSources[ref.pubmed_id][source] = sourceStr;
            }
        }
        this._referenceDBSources = referenceDBSources;
    }

    getReferenceDBSources(pmid) {
        if (!this.hasOwnProperty("_referenceDBSources")) {
            this._createReferenceDBSources()
        }
        return this._referenceDBSources[pmid];
    }

    getAbstract(reference) {
        return "[DEBUG] The vast majority of coding variants are rare, and assessment of the contribution of rare variants to complex traits is hampered by low statistical power and limited functional data. Improved methods for predicting the pathogenicity of rare coding variants are needed to facilitate the discovery of disease variants from exome sequencing studies. We developed REVEL (rare exome variant ensemble learner), an ensemble method for predicting the pathogenicity of missense variants on the basis of individual tools: MutPred, FATHMM, VEST, PolyPhen, SIFT, PROVEAN, MutationAssessor, MutationTaster, LRT, GERP, SiPhy, phyloP, and phastCons. REVEL was trained with recently discovered pathogenic and rare neutral missense variants, excluding those previously used to train its constituent tools. When applied to two independent test sets, REVEL had the best overall performance (p < 10-12) as compared to any individual tool and seven ensemble methods: MetaSVM, MetaLR, KGGSeq, Condel, CADD, DANN, and Eigen. Importantly, REVEL also had the best performance for distinguishing pathogenic from rare neutral variants with allele frequencies <0.5%. The area under the receiver operating characteristic curve (AUC) for REVEL was 0.046-0.182 higher in an independent test set of 935 recent SwissVar disease variants and 123,935 putatively neutral exome sequencing variants and 0.027-0.143 higher in an independent test set of 1,953 pathogenic and 2,406 benign variants recently reported in ClinVar than the AUCs for other ensemble methods. We provide pre-computed REVEL scores for all possible human missense variants to facilitate the identification of pathogenic variants in the sea of rare variants discovered as sequencing studies expand in scale."
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
