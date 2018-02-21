import { Compute } from 'cerebral'
import { state, props } from 'cerebral/tags'
import filterClassified from '../../computed/filterClassified'

import isHomozygous from '../computed/isHomozygous'
import isLowQual from '../computed/isLowQual'
import isImportantSource from '../computed/isImportantSource'
//import getClassification from '../computed/getClassification'

function getSortFunctions(config, isHomozygous, isImportantSource, isLowQual, classification) {
    return {
        inheritance: allele => {
            if (allele.formatted.inheritance === 'AD') {
                return '1'
            }
            return allele.formatted.inheritance
        },
        gene: allele => {
            return allele.annotation.filtered[0].symbol
        },
        hgvsc: allele => {
            let s = allele.annotation.filtered[0].HGVSc_short || allele.formatted.hgvsg
            let d = parseInt(s.match(/[cg]\.(\d+)/)[1])
            return d
        },
        consequence: allele => {
            let consequence_priority = config.transcripts.consequences
            let consequences = allele.annotation.filtered.map(t => t.consequences)
            consequences = [].concat.apply([], consequences)
            let consequence_indices = consequences.map(c => consequence_priority.indexOf(c))
            return Math.min(...consequence_indices)
        },
        homozygous: allele => {
            return isHomozygous[allele.id] ? -1 : 1
        },
        quality: allele => {
            return isLowQual[allele.id] ? -1 : 1
        },
        references: allele => {
            return !isImportantSource[allele.id]
        },
        '3hetAR': allele => {
            return 0
            return !this.is3hetAR(allele)
        },
        classification: allele => {
            return classification[allele.id]
        }
    }
}

export default function sortSections({ state, props, resolve }) {
    const orderBy = state.get('views.workflows.alleleSidebar.orderBy')
    const config = state.get('app.config')
    const alleles = state.get('views.workflows.data.alleles')

    const unclassified = resolve.value(filterClassified(true, alleles))
    const classified = resolve.value(filterClassified(false, alleles))

    const sortFunctions = getSortFunctions(
        config,
        resolve.value(isHomozygous),
        resolve.value(isImportantSource),
        resolve.value(isLowQual),
        {} //resolve.value(getClassification),
    )

    if (orderBy.unclassified.key) {
        unclassified.sort(
            firstBy(sortFunctions[orderBy.unclassified.key], orderBy.unclassified.reverse ? -1 : 1)
                .thenBy(sortFunctions.inheritance)
                .thenBy(sortFunctions.gene)
                .thenBy(sortFunctions.hgvsc)
        )
    } else {
        unclassified.sort(
            firstBy(sortFunctions.inheritance)
                .thenBy(sortFunctions.gene)
                .thenBy(sortFunctions.hgvsc)
        )
    }

    if (orderBy.classified.key) {
        classified.sort(
            firstBy(sortFunctions[orderBy.classified.key], orderBy.classified.reverse ? -1 : 1)
                .thenBy(sortFunctions.inheritance)
                .thenBy(sortFunctions.gene)
                .thenBy(sortFunctions.hgvsc)
        )
    } else {
        classified.sort(
            firstBy(sortFunctions.classification, -1)
                .thenBy(sortFunctions.inheritance)
                .thenBy(sortFunctions.gene)
                .thenBy(sortFunctions.hgvsc)
        )
    }

    state.set('views.workflows.alleleSidebar.unclassified', unclassified.map(a => a.id))
    state.set('views.workflows.alleleSidebar.classified', classified.map(a => a.id))
}
