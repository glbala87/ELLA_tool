import thenBy from 'thenby'
import { state } from 'cerebral/tags'
import { Compute } from 'cerebral'
import getClassification from '../alleleSidebar/computed/getClassification'
import getVerificationStatus from '../interpretation/computed/getVerificationStatus'

function getSortFunctions(config, classification, verificationStatus) {
    return {
        inheritance: (allele) => {
            if (allele.formatted.inheritance === 'AD') {
                return '1'
            }
            return allele.formatted.inheritance
        },
        gene: (allele) => {
            if (allele.annotation.filtered && allele.annotation.filtered.length) {
                return allele.annotation.filtered[0].symbol
            }
            return -1
        },
        hgvsc: (allele) => {
            if (allele.annotation.filtered && allele.annotation.filtered.length) {
                const s = allele.annotation.filtered[0].HGVSc_short || allele.formatted.hgvsg
                const pos = s.match(/[cg]\.(\d+)/)
                return pos ? parseInt(pos[1]) : 0
            }
            return -1
        },
        consequence: (allele) => {
            let consequence_priority = config.transcripts.consequences
            let consequences = allele.annotation.filtered.map((t) => t.consequences)
            consequences = [].concat.apply([], consequences)
            let consequence_indices = consequences.map((c) => consequence_priority.indexOf(c))
            return Math.min(...consequence_indices)
        },
        segregation: (allele) => {
            if (allele.tags.includes('denovo')) {
                return 0
            } else if (allele.tags.includes('autosomal_recessive_homozygous')) {
                return 1
            } else if (allele.tags.includes('xlinked_recessive_homozygous')) {
                return 2
            } else if (allele.tags.includes('recessive_compound_heterozygous')) {
                return 3
            } else {
                return 4
            }
        },
        homozygous: (allele) => {
            return allele.tags.includes('homozygous') ? -1 : 1
        },
        quality: (allele) => {
            if (verificationStatus[allele.id] === 'verified') {
                return 0
            } else if (verificationStatus[allele.id] === 'technical') {
                return 3
            } else if (allele.tags.includes('low_quality')) {
                return 2
            } else {
                return 1
            }
        },
        references: (allele) => {
            return allele.tags.includes('has_references') ? -1 : 1
        },
        technical: (allele) => {
            return verificationStatus[allele.id] === 'technical' ? 1 : -1
        },
        classification: (allele) => {
            return config.classification.options.findIndex(
                (o) => o.value === classification[allele.id].classification
            )
        },
        warning: (allele) => {
            return allele.warnings ? -1 : 1
        }
    }
}

export default function sortAlleles(alleles, key, reverse) {
    return Compute(
        alleles,
        key,
        reverse,
        state`app.config`,
        (alleles, key, reverse, config, get) => {
            if (!alleles) {
                return
            }
            const sortedAlleles = Object.values(alleles).slice()
            const sortFunctions = getSortFunctions(
                config,
                get(getClassification),
                get(getVerificationStatus(alleles))
            )

            if (key === 'classification') {
                sortedAlleles.sort(
                    thenBy(sortFunctions.technical)
                        .thenBy(sortFunctions.classification, -1)
                        .thenBy(sortFunctions.inheritance)
                        .thenBy(sortFunctions.gene)
                        .thenBy(sortFunctions.hgvsc)
                )
            } else if (key) {
                sortedAlleles.sort(
                    thenBy(sortFunctions[key], reverse ? -1 : 1)
                        .thenBy(sortFunctions.inheritance)
                        .thenBy(sortFunctions.gene)
                        .thenBy(sortFunctions.hgvsc)
                )
            } else {
                sortedAlleles.sort(
                    thenBy(sortFunctions.segregation)
                        .thenBy(sortFunctions.inheritance)
                        .thenBy(sortFunctions.gene)
                        .thenBy(sortFunctions.hgvsc)
                )
            }
            return sortedAlleles
        }
    )
}
