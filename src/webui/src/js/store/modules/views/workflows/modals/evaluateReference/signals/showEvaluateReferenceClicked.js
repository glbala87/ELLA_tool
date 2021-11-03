import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import { deepCopy } from '../../../../../../../util'
import getReferenceAssessment from '../../../interpretation/computed/getReferenceAssessment'
// import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'

const STATE_BASE = 'views.workflows.modals.evaluateReference'

export default [
    set(state`${STATE_BASE}.show`, true),
    set(state`${STATE_BASE}.referenceId`, props`referenceId`),
    // Get reference data
    set(
        state`${STATE_BASE}.reference`,
        deepCopy(state`views.workflows.interpretation.data.references.${props`referenceId`}`)
    ),
    // Get annotation sources (USER, CLINVAR etc)
    ({ state }) => {
        const selectedAlleleId = state.get('views.workflows.selectedAllele')
        const reference = state.get(`${STATE_BASE}.reference`)
        const annotationSources = state
            .get(
                `views.workflows.interpretation.data.alleles.${selectedAlleleId}.annotation.references`
            )
            .filter((r) => r.id === reference.id || r.pubmed_id === reference.pubmed_id)
            .map((r) => r.source)
        state.set(`${STATE_BASE}.annotationSources`, annotationSources)
    },
    // Deep copy existing referenceassessment to modal
    ({ state, resolve }) => {
        const selectedAlleleId = state.get('views.workflows.selectedAllele')
        const reference = state.get(`${STATE_BASE}.reference`)
        const referenceAssessment = deepCopy(
            resolve.value(getReferenceAssessment(selectedAlleleId, reference.id)) || {}
        )

        // Set up basic structure if empty
        if (!referenceAssessment.evaluation) {
            referenceAssessment.evaluation = {}
        }
        if (!referenceAssessment.evaluation.sources) {
            referenceAssessment.evaluation.sources = []
        }
        if (!referenceAssessment.evaluation.relevance) {
            referenceAssessment.evaluation.relevance = 'Yes'
        }
        state.set(`${STATE_BASE}.referenceAssessment`, referenceAssessment)
    },
    // Compute gene groups for allele, which is used to determine if certain selections are available
    ({ state }) => {
        const geneGroups = state.get('app.config.classification.gene_groups')
        const selectedAlleleId = state.get('views.workflows.selectedAllele')
        let alleleGenes = state
            .get(
                `views.workflows.interpretation.data.alleles.${selectedAlleleId}.annotation.filtered`
            )
            .map((x) => x.symbol)
        const alleleGeneGroups = Object.keys(geneGroups).filter((k) =>
            geneGroups[k].some((g) => alleleGenes.includes(g))
        )
        state.set(`${STATE_BASE}.alleleGeneGroups`, alleleGeneGroups)
    }
]
