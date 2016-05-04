/* jshint esnext: true */

import Analysis from './analysis';


export class Interpretation {
    /**
     * Represents one Interpretation.
     * @param  {object} Interpretation data from server.
     */
    constructor(data) {
        console.log('Constructor for Interpretation with id=' + data.id);
        Object.assign(this, data);
        if ('analysis' in data) {
            this.analysis = new Analysis(data.analysis);

        }
        this.alleles = [];
        this.references = [];
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
