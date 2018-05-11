/* jshint esnext: true */

import Annotation from './annotation'

export class Allele {
    /**
     * Represents one Allele (aka variant)
     * Properties are copied from incoming data (from server),
     * but some fields are reserved internal usage, like
     * 'existingAlleleAssessment' and 'references'.
     * @param  {object} Allele data from server.
     */
    constructor(data) {
        Object.assign(this, data)
        // Convert pure annotation data to model object
        // check if this.annotation is defined first
        if (this.annotation) {
            this.annotation = new Annotation(this.annotation)
        }
    }

    getReferenceIds() {
        let ids = []
        if (this.annotation) {
            for (let ref of this.annotation.references) {
                ids.push({ id: ref.id, pubmed_id: ref.pubmed_id })
            }
        }
        return Array.from(new Set(ids))
    }

    toString() {
        let hgvs = ''
        if (this.annotation && this.annotation.filtered) {
            for (let t of this.annotation.filtered) {
                if (hgvs !== '') {
                    hgvs += '|'
                }
                hgvs += `${t.transcript}(${t.symbol}):${t.HGVSc_short || this.getHGVSgShort()}`
            }
        }
        return hgvs
    }

    getHGVSgShort() {
        // Database is 0-based, alamut uses 1-based index
        let start = this.start_position
        let end = this.open_end_position
        let result = 'g.'

        if (this.change_type === 'SNP') {
            // snp: Chr11(GRCh37):g.66285951C>Tdel:
            result += `${start + 1}${this.change_from}>${this.change_to}`
        } else if (this.change_type === 'del') {
            // del: Chr13(GRCh37):g.32912008_32912011del
            result += `${start + 1}_${end}del`
        } else if (this.change_type === 'ins') {
            // ins: Chr13(GRCh37):g.32912008_3291209insCGT
            result += `${start}_${start + 1}ins${this.change_to}`
        } else if (this.change_type === 'indel') {
            // delins: Chr13(GRCh37):g.32912008_32912011delinsGGG
            result += `${start + 1}_${end}delins${this.change_to}`
        } else {
            // edge case, shouldn't happen, but this is valid format as well
            result += `${start + 1}`
        }

        return result
    }

    getHGMDUrl() {
        if (
            this.annotation &&
            this.annotation.external &&
            'HGMD' in this.annotation.external &&
            'acc_num' in this.annotation.external.HGMD
        ) {
            let acc_num = this.annotation.external.HGMD.acc_num
            return `https://portal.biobase-international.com/hgmd/pro/mut.php?accession=${acc_num}`
        }
    }

    getClinvarUrl() {
        if (this.annotation && this.annotation.external && 'CLINVAR' in this.annotation.external) {
            let variant_id = this.annotation.external.CLINVAR['variant_id']
            return 'https://www.ncbi.nlm.nih.gov/clinvar/variation/' + variant_id
        }
    }

    getESP6500Url() {
        return `http://evs.gs.washington.edu/EVS/PopStatsServlet?searchBy=chromosome&chromosome=${
            this.chromosome
        }&chromoStart=${this.start_position + 1}&chromoEnd=${this.open_end_position}&x=0&y=0`
    }

    getEnsemblUrl() {
        return `http://grch37.ensembl.org/Homo_sapiens/Location/View?r=${this.chromosome}%3A${this
            .start_position + 1}-${this.open_end_position}`
    }

    /**
     * Filters the list of ACMG codes based on the selector.
     * Selector example: 'frequencies.ExAC'
     */
    getACMGCodes(selector) {
        if (selector) {
            if (this.acmg && this.acmg.codes) {
                return this.acmg.codes.filter((c) => {
                    return c.source === selector
                })
            } else {
                return []
            }
        } else {
            return this.acmg.codes
        }
    }

    /**
     * Returns formatted genotype string for allele.
     * If no sample data is present, an empty string is returned.
     *
     * Otherwise:
     *  - If single sample, return genotype directly: 'A/G'
     *  - If multiple samples, put sample type letter in front: 'S: A/G, H: A/A'
     */
    formatGenotype() {
        let shortGenotype = (match, gt1, gt2) => {
            if (gt1.length >= 10) gt1 = `(${gt1.length})`
            if (gt2.length >= 10) gt2 = `(${gt2.length})`
            return `${gt1}/${gt2}`
        }

        if ('samples' in this) {
            if (this.samples.length > 1) {
                // If multiple, return 'S: A/T, H: A/G'
                return this.samples
                    .map((s) => {
                        return (
                            s.sample_type.substring(0, 1).toUpperCase() +
                            ': ' +
                            s.genotype.genotype.replace(/(.*)\/(.*)/g, shortGenotype)
                        )
                    })
                    .join(', ')
            } else {
                return this.samples[0].genotype.genotype.replace(/(.*)\/(.*)/g, shortGenotype)
            }
        }
        return ''
    }

    /**
     * Returns a string formatted for pasting into Alamut.
     * @param  {Allele} alleles List of alleles to include
     * @return {[type]}         String to paste into Alamut
     */
    formatAlamut() {
        // (Alamut also support dup, but we treat them as indels)
        // (dup: Chr13(GRCh37):g.32912008_3291212dup )

        let result = `Chr${this.chromosome}(${this.genome_reference}):g.`

        // Database is 0-based, alamut uses 1-based index
        let start = this.start_position
        let end = this.open_end_position

        if (this.change_type === 'SNP') {
            // snp: Chr11(GRCh37):g.66285951C>Tdel:
            result += `${start + 1}${this.change_from}>${this.change_to}`
        } else if (this.change_type === 'del') {
            // del: Chr13(GRCh37):g.32912008_32912011del
            result += `${start + 1}_${end}del`
        } else if (this.change_type === 'ins') {
            // ins: Chr13(GRCh37):g.32912008_3291209insCGT
            result += `${start}_${start + 1}ins${this.change_to}`
        } else if (this.change_type === 'indel') {
            // delins: Chr13(GRCh37):g.32912008_32912011delinsGGG
            result += `${start + 1}_${end}delins${this.change_to}`
        } else {
            // edge case, shouldn't happen, but this is valid format as well
            result += `${start + 1}`
        }

        return result
    }

    formatGenomicPosition() {
        if (this.change_type === 'SNP') {
            return `${this.chromosome}:${this.start_position + 1}`
        } else if (this.change_type === 'del') {
            if (this.change_from.length > 1) {
                return `${this.chromosome}:${this.start_position + 1}-${this.open_end_position}`
            } else {
                return `${this.chromosome}:${this.start_position + 1}`
            }
        } else if (this.change_type === 'ins') {
            return `${this.chromosome}:${this.start_position}-${this.start_position + 1}`
        } else {
            return `${this.chromosome}:${this.start_position + 1}-${this.open_end_position}`
        }
    }

    getWorkflowUrl(genepanel) {
        return (
            `/variants/${this.genome_reference}/` +
            `${this.chromosome}-${this.vcf_pos}-${this.vcf_ref}-${this.vcf_alt}` +
            `?gp_name=${genepanel.name}&gp_version=${genepanel.version}&allele_id=${this.id}`
        )
    }
}
