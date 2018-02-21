import { Compute } from 'cerebral'
import { state, props } from 'cerebral/tags'
import isHomozygous from './isHomozygous'
import isLowQual from './isLowQual'
import isImportantSource from './isImportantSource'

const SORT_FUNCTIONS = {
    inheritance: (allele, config) => {
        return allele.formatted.inheritance
    },
    gene: (allele, config) => {
        return allele.annotation.filtered[0].symbol
    },
    hgvsc: (allele, config) => {
        let s = allele.annotation.filtered[0].HGVSc_short || allele.formatted.hgvsg
        let d = parseInt(s.match(/[cg]\.(\d+)/)[1])
        return d
    },
    consequence: (allele, config) => {
        let consequence_priority = config.transcripts.consequences
        let consequences = allele.annotation.filtered.map(t => t.consequences)
        consequences = [].concat.apply([], consequences)
        let consequence_indices = consequences.map(c => consequence_priority.indexOf(c))
        return Math.min(...consequence_indices)
    },
    homozygous: (allele, config) => {
        return !isHomozygous(allele)
    },
    quality: (allele, config) => {
        return !isLowQual(allele)
    },
    references: (allele, config) => {
        return !isImportantSource(allele)
    },
    '3hetAR': (allele, config) => {
        return 0
        return !this.is3hetAR(allele)
    }
}

export default function sortAlleleSidebar(alleles, key) {
    return Compute(alleles, key, state`app.config`, (alleles, key, config) => {
        if (key in SORT_FUNCTIONS) {
            return alleles.sort(SORT_FUNCTIONS[key])
        }
        return alleles
    })
}
