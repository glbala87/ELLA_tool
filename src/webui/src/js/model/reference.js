/* jshint esnext: true */

export class Reference {
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


export class ReferenceAssessment {

    constructor(data) {
        console.log(data);
        this.id = data.allele_id.toString() + '_' + data.reference_id.toString();
        this.allele_id = data.allele_id;
        this.reference_id = data.reference_id;
        this.evaluation = data.evaluation || {};
        this.sources = '';
    }

    setSources(sources) {
        this.sources = sources;
    }
}
