/* jshint esnext: true */

import Annotation from './annotation';

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

    getExACUrl() {
        return `http://exac.broadinstitute.org/variant/${this.chromosome}-${this.vcfPos}-${this.vcfRef}-${this.vcfAlt}`;
    }

    getDbSNPUrl(dbsnp) {
        return `http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=${dbsnp}`;
    }

    getHGMDUrl() {
        if ('HGMD' in this.annotation.external &&
            'acc_num' in this.annotation.external.HGMD) {
            let acc_num = this.annotation.external.HGMD.acc_num;
            return `https://portal.biobase-international.com/hgmd/pro/mut.php?accession=${acc_num}`
        }
    }

    getClinvarUrl() {
        if ('CLINVAR' in this.annotation.external &&
            'CLNACC' in this.annotation.external.CLINVAR) {
            let search_term = this.annotation.external.CLINVAR.CLNACC.split('|').map(s => s.split('.')[0]).join(' OR ');
            return `http://www.ncbi.nlm.nih.gov/clinvar?term=${search_term}`;
        }
    }

}
