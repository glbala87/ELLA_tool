import thenBy from 'thenby'
import { state } from 'cerebral/tags'
import { Compute } from 'cerebral'
import getClassificationById from '../alleleSidebar/computed/getClassificationById'
import getVerificationStatusById from '../alleleSidebar/computed/getVerificationStatusById'
import getDepthById from '../alleleSidebar/computed/getDepthById'
import getAlleleRatioById from '../alleleSidebar/computed/getAlleleRatioById'
import getHiFrequencyById from '../alleleSidebar/computed/getHiFrequencyById'
import getExternalSummaryById from '../alleleSidebar/computed/getExternalSummaryById'
import getQualById from '../alleleSidebar/computed/getQualById'
import isManuallyAddedById from '../alleleSidebar/computed/isManuallyAddedById'

function getSortFunctions(
    config,
    classification,
    verificationStatus,
    qual,
    readDepth,
    alleleRatio,
    hiFreq,
    hiCount,
    externalSummary,
    manuallyAdded
) {
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
            if (allele.tags.includes('inherited_mosaicism')) {
                return 0
            } else if (allele.tags.includes('denovo')) {
                return 1
            } else if (allele.tags.includes('autosomal_recessive_homozygous')) {
                return 2
            } else if (allele.tags.includes('xlinked_recessive_homozygous')) {
                return 3
            } else if (allele.tags.includes('compound_heterozygous')) {
                return 4
            } else {
                return 5
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
        },
        qual: (allele) => {
            if (allele.id in qual) {
                const q = parseInt(qual[allele.id].split(',')[0])
                return isNaN(q) ? 1 : -q
            }
            return 0
        },
        readDepth: (allele) => {
            if (allele.id in readDepth) {
                const dp = parseInt(readDepth[allele.id].split(',')[0])
                return isNaN(dp) ? 1 : -dp
            }
            return 0
        },
        ratio: (allele) => {
            if (allele.id in alleleRatio) {
                const ar = parseFloat(alleleRatio[allele.id].split(',')[0])
                return isNaN(ar) ? 1 : -ar
            }
            return 0
        },
        freq: (allele) => {
            const f = hiFreq[allele.id]
            if (f && f.maxMeetsThresholdValue) {
                return -f.maxMeetsThresholdValue
            } else if (f && f.maxValue) {
                return -f.maxValue
            } else {
                return 1
            }
        },
        count: (allele) => {
            const c = hiCount[allele.id]
            if (c && c.maxMeetsThresholdValue) {
                return -c.maxMeetsThresholdValue
            } else if (c && c.maxValue) {
                return -c.maxValue
            } else {
                return 1
            }
        },
        external: (allele) => {
            if (allele.id in externalSummary) {
                return -externalSummary[allele.id].length
            }
            return 0
        },
        manuallyAdded: (allele) => {
            return manuallyAdded[allele.id] ? -1 : 1
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

            const allelesById = {}
            for (let allele of alleles) {
                allelesById[allele.id] = allele
            }
            const sortFunctions = getSortFunctions(
                config,
                get(getClassificationById(allelesById)),
                get(getVerificationStatusById(allelesById)),
                get(getQualById(allelesById)),
                get(getDepthById(allelesById)),
                get(getAlleleRatioById(allelesById)),
                get(getHiFrequencyById(allelesById, 'freq')),
                get(getHiFrequencyById(allelesById, 'count')),
                get(getExternalSummaryById(allelesById)),
                get(isManuallyAddedById(allelesById))
            )

            const sortedAlleles = Object.values(alleles).slice()

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
