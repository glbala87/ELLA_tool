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
        this.serverReferenceassessments = [];
        this.referenceassessments = [];
        this.serverAlleleassessments = [];
        this.alleleassessments = [];
        this.references = [];
        this.userState = data.userState;
        this.state = data.state;
        this.dirty = false; // Indicates whether any state has changed, so user should save

    }

    /**
     * Call this function whenever the Interpretation's state has been updated.
     * It sets up the internal structures according to the state.
     */
    stateChanged() {

        this.dirty = true;
        // Insert 'Accepted' alleleassessments into generated list
        for (let [allele_id, state] of Object.entries(this.state)) {
            if (this.state[allele_id].vardb &&
                this.state[allele_id].vardb.alleleassessment) {
                this.useAlleleAssessment(this.state[allele_id].vardb.alleleassessment);
            }
        }

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

        this.serverReferenceassessments = referenceassessments;
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
            }
            else {
                this.referenceassessments.push(ra);
            }
        }

        // Create missing entries if not created already
        for (let allele of this.alleles) {
            let pmids = allele.getPubmedIds();
            let reference = this.references.find(ref =>{
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

    _createAlleleAssessment(allele) {
        return {
            allele_id: allele.id,
            allele: allele,
            annotation_id: allele.annotation.id,
            genepanelName: this.analysis.genepanel.name,
            genepanelVersion: this.analysis.genepanel.version,
            interpretation_id: this.id,
            status: 0,
            classification: {},
            comment: null
        };
    }

    /**
     * Searches for alleleassessment in internal list matching id, copying data from server one
     * into the one in the internal list. This will set the status to curated (1) and ensure data
     * is the same as the server one.
     * @param  {[type]} alleleassessment_id Id of alleleassessment to use (present in server list)
     */
    useAlleleAssessment(alleleassessment_id) {
        let server_aa = this.serverAlleleassessments.find(
            elem => elem.id === alleleassessment_id
        );
        if (!server_aa) {
            throw "Couldn't find alleleassessment for requested id. This is a bug or it suddenly is missing from server!";
        }
        let alleleassessment = this.alleleassessments.find(
            elem => elem.id === alleleassessment_id
        );

        if (alleleassessment) {
            Object.assign(alleleassessment, server_aa);
        }

    }

    /**
     * Populates the internal list of AlleleAssessments with incoming data.
     * For the incoming entries, we create an non-curated copy of of the entry by
     * copying the data and setting status to 0.
     * For any missing entries (from server), we create empty ones.
     * @param {Array} alleleassessments Array of AlleleAssessments (should originate from server)
     */
    setAlleleAssessments(alleleassessments) {

        this.serverAlleleassessments = alleleassessments;

        // Refresh the existing list with updated entries.
        for (let aa of alleleassessments) {
            aa.allele = this.alleles.find(al => al.id === aa.allele_id);
            let aa_copy = Object.assign({}, aa); // TODO: Perform deep copy (due to aa.evaluation)
            aa_copy.status = 0;
            let existing = this.alleleassessments.find(elem => {
                return elem.annotation_id === aa_copy.annotation_id &&
                       elem.allele_id === aa_copy.allele_id;
            });
            if (existing) {
                Object.assign(existing, aa_copy);
            }
            else {
                this.alleleassessments.push(aa_copy);
            }
        }

        // Create missing entries
        for (let allele of this.alleles) {
            let existing = this.alleleassessments.find(elem => elem.allele_id === allele.id);
            if (!existing) {
                this.alleleassessments.push(this._createAlleleAssessment(allele));
            }
        }
    }

}
