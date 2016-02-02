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
        this.references = [];
        this.userState = data.userState;
        this.state = data.state;
        this.user_id = data.user_id;
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
}
