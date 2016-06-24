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
        if ('ExAC' in this.annotation.frequencies &&
            this.chromosome &&
            this.genotype) {
            return `http://exac.broadinstitute.org/variant/${this.chromosome}-${this.genotype.vcfPos}-${this.genotype.vcfRef}-${this.genotype.vcfAlt}`;
        }
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

    get1000gUrl() {
        if ('1000g' in this.annotation.frequencies) {
            return `http://browser.1000genomes.org/Homo_sapiens/Location/View?db=core;r=${this.chromosome}:${this.startPosition+1}-${this.openEndPosition}`
        }
    }

    getESP6500Url() {
        if ('esp6500' in this.annotation.frequencies) {
            return `http://evs.gs.washington.edu/EVS/PopStatsServlet?searchBy=chromosome&chromosome=${this.chromosome}&chromoStart=${this.startPosition+1}&chromoEnd=${this.openEndPosition}&x=0&y=0`
        }
    }

    /**
     * Convenience function for getting the urls dynamically.
     * Used by allelecardcontent to get the header links.
     */
    getUrl(type) {
        let types = {
            'ExAC': () => this.getExACUrl(),
            'HGMD Pro': () => this.getHGMDUrl(),
            'Clinvar': () => this.getClinvarUrl(),
            '1000g': () => this.get1000gUrl(),
            'ESP6500': () => this.getESP6500Url()
        }
        if (type in types) {
            return types[type]();
        }
        return '';
    }

    /**
     * Filters the list of ACMG codes based on the selector.
     * Selector example: 'frequencies.ExAC'
     */
    getACMGCodes(selector) {
        if (selector) {
            if (this.acmg &&
                this.acmg.codes) {
                return this.acmg.codes.filter(c => {
                    return c.source === selector;
                });
            }
            else {
                return [];
            }
        }
        else {
            return this.acmg.codes;
        }
    }
}
