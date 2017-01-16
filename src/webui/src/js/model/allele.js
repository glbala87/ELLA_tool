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
        this._createAnnotations();
    }

    _createAnnotations() {
        // Convert pure annotation data to model object
        this.annotation = new Annotation(this.annotation);
    }

    getPubmedIds() {
        let ids = [];
        for (let ref of this.annotation.references) {
            ids.push(parseInt(ref.pubmed_id, 10));
        }
        return Array.from(new Set(ids));
    }

    toString() {
        let hgvs = '';
        for (let t of this.annotation.filtered) {
            if (hgvs !== '') {
                hgvs += '|'
            }
            hgvs += `${t.transcript}(${t.symbol}):${t.HGVSc_short}`;
        }
        return hgvs;
    }

    getExACUrl() {
        if (this.chromosome) {
            return `http://exac.broadinstitute.org/region/${this.chromosome}-${this.start_position - 9}-${this.open_end_position + 10}`;
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
        if ('CLINVAR' in this.annotation.external) {
            let variant_id = this.annotation.external.CLINVAR[0]["variant_id"];
            return "https://www.ncbi.nlm.nih.gov/clinvar/variation/" + variant_id;
        }
    }

    get1000gUrl() {
        return `http://browser.1000genomes.org/Homo_sapiens/Location/View?db=core;r=${this.chromosome}:${this.start_position+1}-${this.open_end_position}`
    }

    getESP6500Url() {
        return `http://evs.gs.washington.edu/EVS/PopStatsServlet?searchBy=chromosome&chromosome=${this.chromosome}&chromoStart=${this.start_position+1}&chromoEnd=${this.open_end_position}&x=0&y=0`
    }

    getEnsemblUrl() {
        return `http://grch37.ensembl.org/Homo_sapiens/Location/View?r=${this.chromosome}%3A${this.start_position+1}-${this.open_end_position}`
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

    /**
     * Returns a string formatted for pasting into Alamut.
     * @param  {Allele} alleles List of alleles to include
     * @return {[type]}         String to paste into Alamut
     */
    formatAlamut() {

        // (Alamut also support dup, but we treat them as indels)
        // (dup: Chr13(GRCh37):g.32912008_3291212dup )

        let result = `Chr${this.chromosome}(${this.genome_reference}):g.`;

        // Database is 0-based, alamut uses 1-based index
        let start = this.start_position + 1;
        let end = this.open_end_position + 1;

        if (this.change_type === 'SNP') {
            // snp: Chr11(GRCh37):g.66285951C>Tdel:
            result += `${start}${this.change_from}>${this.change_to}`;
        }
        else if (this.change_type === 'del') {
            // del: Chr13(GRCh37):g.32912008_32912011del
            result += `${start}_${end}del`;
        }
        else if (this.change_type === 'ins') {
            // ins: Chr13(GRCh37):g.32912008_3291209insCGT
            result += `${start}_${start+1}ins${this.change_to}`;
        }
        else if (this.change_type === 'indel') {
            // delins: Chr13(GRCh37):g.32912008_32912011delinsGGG
            result += `${start}_${end}delins${this.change_to}`;
        }
        else {
            // edge case, shouldn't happen, but this is valid format as well
            result += `${start}`;
        }

        return result;
    }

    formatGenomicPosition() {
        if (this.change_type === 'SNP') {
            return `${this.chromosome}:${this.start_position+1}`;
        }
        else if (this.change_type === 'del') {
            if (this.change_from.length > 1) {
                return `${this.chromosome}:${this.start_position+1}-${this.open_end_position+1}`;
            }
            else {
                return `${this.chromosome}:${this.start_position+1}`;
            }
        }
        else if (this.change_type === 'ins') {
            return `${this.chromosome}:${this.start_position}-${this.start_position+1}`;
        }
        else {
            return `${this.chromosome}:${this.start_position+1}-${this.open_end_position+1}`;
        }
    }
}
