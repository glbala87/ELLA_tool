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

    setClean() {
        this.dirty = false;
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

    setReferenceAssessments(referenceassessments) {
        this.referenceassessments = referenceassessments;
    }

    setAlleleAssessments(alleleassessments) {
        this.alleleassessments = alleleassessments;

        for (let aa of this.alleleassessments) {
            aa.allele = this.alleles.find(a => aa.allele_id === a.id);
        }
    }

}
