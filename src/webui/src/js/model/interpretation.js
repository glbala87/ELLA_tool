/* jshint esnext: true */

export class Interpretation {
    /**
     * Represents one Interpretation.
     * @param  {object} Interpretation data from server.
     */
    constructor(data) {
        this.id = data.id;
        this.status = data.status;
        this.analysis = data.analysis;
        this.dateLastUpdate = data.dateLastUpdate;
        this.alleles = [];
        this.userState = data.userState;
        this.state = data.state;
        this.dirty = false; // Indicates whether any state has changed, so user should save

    }

    /**
     * Call this function whenever the Interpretation's state has been updated.
     */
    setDirty() {
        this.dirty = true;
    }

    setClean() {
        this.dirty = false;
    }

    setAlleles(alleles) {
        this.alleles = alleles;
    }

    /**
     * Helper method for preparing the Allele objects.
     */
    prepareAlleles(references,
                   existingReferenceAssessments,
                   existingAlleleAssessments) {

        for (let allele of this.alleles) {
            let pmids = allele.getPubmedIds();

            // Set references
            let allele_refs = references.filter(ref => {
                return pmids.find(pmid => ref.pubmedID == pmid) !== undefined;
            });
            allele.setReferences(allele_refs);

            // Set referenceassessments (must be done after references)
            allele.setReferenceAssessments(existingReferenceAssessments.filter(era => {
                return era.allele_id === allele.id;
            }));

            // Set alleleassessments (assume one per allele)
            allele.setAlleleAssessment(existingAlleleAssessments.filter(aa => {
                return aa.allele_id === allele.id;
            })[0]);
        }
    }
}
