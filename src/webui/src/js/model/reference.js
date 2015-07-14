/* jshint esnext: true */

class Reference {
    /**
     * Represents one Reference
     * @param  {object} Reference data from server.
     */
    constructor(data) {
        Object.assign(this, data);
    }

    getShortDesc() {
        return `${this.authors} (${this.year}) ${this.journal}`;
    }
}


class ReferenceAssessment {

    constructor(allele, reference) {
        this.id = allele.id.toString() + reference.id.toString();
        this.allele = allele;
        this.reference = reference;
        this.evaluation = {};
        this.sources = '';
    }

    setSources(sources) {
        this.sources = sources;
    }
}
