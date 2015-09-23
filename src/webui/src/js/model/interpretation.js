/* jshint esnext: true */

class Interpretation {
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
        this.referenceassessments = [];
        this.alleleassessments = [];
        this.references = [];
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

    setAlleles(alleles) {
        this.alleles = [];
        for (let allele of alleles) {
            this.alleles.push(new Allele(allele));
        }
        console.log(this);
    }

    setReferences(references) {
        this.references = references;
    }

    _createReferenceAssessment(allele, reference) {
        return {
            allele_id: allele.id,
            allele,
            reference_id: reference.id,
            reference,
            genepanelName: this.analysis.genepanel.name,
            genepanelVersion: this.analysis.genepanel.version,
            interpretation_id: this.id,
            evaluation: {}
        };
    }

    /**
     * Populates the internal list of ReferenceAssessments with incoming data.
     * For the missing entries (not part of incoming data), we create empty ones, to be filled out by user.
     * @param {Array} referenceassessments Array of referenceassessments (should originate from server).
     */
    setReferenceAssessments(referenceassessments) {

        // Refresh the existing list with updated entries.
        for (let ra of referenceassessments) {
            // Insert Allele and Reference objects
            ra.allele = this.alleles.find(al => al.id === ra.allele_id);
            ra.reference = this.references.find(ref => ref.id === ra.reference_id);
            let existing = this.referenceassessments.find(elem => {
                return elem.allele_id === ra.allele_id &&
                    elem.reference_id === ra.reference_id;
            });
            if (existing) {
                // Copy all values from new into old object
                Object.assign(existing, ra);
            } else {
                this.referenceassessments.push(ra);
            }
        }

        // Create missing entries if not created already
        for (let allele of this.alleles) {
            let pmids = allele.getPubmedIds();
            let reference = this.references.find(ref => {
                return pmids.indexOf(ref.pubmedID) !== -1;
            });
            if (reference) {
                // Check if we have data for this entry already
                let match = this.referenceassessments.find(ra => {
                    return ra.allele_id === allele.id &&
                        ra.reference_id === reference.id;
                });
                if (!match) {
                    this.referenceassessments.push(
                        this._createReferenceAssessment(allele, reference)
                    );
                }
            }
        }
    }

    /**
     * Populates the internal list of AlleleAssessments with incoming data.
     * For each entry we insert the allele property with the belonging allele.
     * @param {Array} alleleassessments Array of AlleleAssessments (should originate from server)
     */
    setAlleleAssessments(alleleassessments) {

        this.alleleassessments = alleleassessments;

        // Refresh the existing list with updated entries.
        for (let aa of alleleassessments) {
            aa.allele = this.alleles.find(al => al.id === aa.allele_id);
        }

    }

}
