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
        let desc = this.authors;
        if (this.year !== undefined && this.year.length > 0) {
            desc += ` (${this.year})`
        }
        desc += `, ${this.journal}`
        return desc
    }
    
    getPubmedUrl(pmid) {
        return `http://www.ncbi.nlm.nih.gov/pubmed/${pmid}`;
    }

    getPubmedLink() {
      if(this.hasOwnProperty('pubmed_id') && this.pubmed_id !== '')
        return this.getPubmedUrl(this.pubmed_id);
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
