/* jshint esnext: true */

class Allele {
    /**
     * Represents one Allele (aka variant)
     * @param  {object} Allele data from server.
     */
    constructor(data) {
        Object.assign(this, data);
        this._createAnnotations();
    }

    _createAnnotations() {
        this.annotation = new Annotation(this.annotation);
    }

    getPubmedIds() {
        let ids = [];
        for (let ref of this.annotation.annotations.references) {
            ids.push(ref.pubmedID);
        }
        return ids;
    }
}
