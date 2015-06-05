/* jshint esnext: true */

class Reference {
    /**
     * Represents one Reference
     * @param  {object} Reference data from server.
     */
    constructor(data) {
        Object.assign(this, data);
        this._data = data;
        this.allele = null;  // Metadata: Allele obj referencing this resource
        this.sources = [];  // Metadata: Sources where this reference was found
    }

    copy() {
        return new Reference(this._data);
    }

    setAllele(allele) {
        this.allele = allele;
    }

    setSources(sources) {
        this.sources = sources;
    }

    getShortDesc() {
        return `${this.authors} (${this.year}) ${this.journal}`;
    }
}
