/* jshint esnext: true */

import {Annotation} from './annotation';

export class Allele {
    /**
     * Represents one Allele (aka variant)
     * Properties are copied from incoming data (from server),
     * but some fields are reserved internal usage, like
     * 'existingAlleleAssessment' and 'references'.
     * @param  {object} Allele data from server.
     */
    constructor(data) {
        Object.assign(this, data);
        this.acmg = {};
        this._createAnnotations();
    }

    _createAnnotations() {
        // Convert pure annotation data to model object
        this.annotation = new Annotation(this.annotation);
    }

    getPubmedIds() {
        let ids = [];
        for (let ref of this.annotation.references) {
            ids.push(parseInt(ref.pubmedID, 10));
        }
        return Array.from(new Set(ids));
    }

    toString() {
        let hgvs = '';
        for (let t of this.annotation.filtered) {
            if (hgvs !== '') {
                hgvs += '|'
            }
            hgvs += `${t.Transcript}.${t.Transcript_version}(${t.SYMBOL}):${t.HGVSc_short}`;
        }
        return hgvs;
    }

}
