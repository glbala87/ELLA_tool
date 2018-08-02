import thenBy from 'thenby'
import { state } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isHomozygous from '../alleleSidebar/computed/isHomozygous'
import isLowQual from '../alleleSidebar/computed/isLowQual'
import hasReferences from '../alleleSidebar/computed/hasReferences'
import getClassification from '../alleleSidebar/computed/getClassification'
import getVerificationStatus from '../interpretation/computed/getVerificationStatus'

function getSortFunctions(
    config,
    isHomozygous,
    hasReferences,
    isLowQual,
    classification,
    verificationStatus
) {
    return {
        inheritance: (allele) => {
            if (allele.formatted.inheritance === 'AD') {
                return '1'
            }
            return allele.formatted.inheritance
        },
        gene: (allele) => {
            return allele.annotation.filtered[0].symbol
        },
        hgvsc: (allele) => {
            const s = allele.annotation.filtered[0].HGVSc_short || allele.formatted.hgvsg
            const pos = s.match(/[cg]\.(\d+)/)
            return pos ? parseInt(pos[1]) : 0
        },
        consequence: (allele) => {
            let consequence_priority = config.transcripts.consequences
            let consequences = allele.annotation.filtered.map((t) => t.consequences)
            consequences = [].concat.apply([], consequences)
            let consequence_indices = consequences.map((c) => consequence_priority.indexOf(c))
            return Math.min(...consequence_indices)
        },
        homozygous: (allele) => {
            return isHomozygous[allele.id] ? -1 : 1
        },
        quality: (allele) => {
            if (verificationStatus[allele.id] === 'verified') {
                return 0
            } else if (verificationStatus[allele.id] === 'technical') {
                return 3
            } else if (isLowQual[allele.id]) {
                return 2
            } else {
                return 1
            }
        },
        references: (allele) => {
            return !hasReferences[allele.id]
        },
        '3hetAR': (allele) => {
            return 0 // FIXME
            return !this.is3hetAR(allele)
        },
        technical: (allele) => {
            return verificationStatus[allele.id] === 'technical' ? 1 : -1
        },
        classification: (allele) => {
            return config.classification.options.findIndex(
                (o) => o.value === classification[allele.id]
            )
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
                get(isHomozygous),
                get(hasReferences),
                get(isLowQual),
                get(getClassification),
                get(getVerificationStatus)
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
                    thenBy(sortFunctions.inheritance)
                        .thenBy(sortFunctions.gene)
                        .thenBy(sortFunctions.hgvsc)
                )
            }
            return sortedAlleles
        }
    )
}
