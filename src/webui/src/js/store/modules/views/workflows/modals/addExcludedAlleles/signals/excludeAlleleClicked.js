import loadExcludedAlleles from '../sequences/loadExcludedAlleles'
import loadIncludedAlleles from '../sequences/loadIncludedAlleles'

export default [
    ({ state, props }) => {
        const includedAlleleIds = state.get(
            'views.workflows.modals.addExcludedAlleles.includedAlleleIds'
        )
        const idx = includedAlleleIds.findIndex((alleleId) => alleleId === props.alleleId)
        if (idx >= 0) {
            state.splice(`views.workflows.modals.addExcludedAlleles.includedAlleleIds`, idx, 1)
        } else {
            throw Error(`Allele id ${props.alleleId} is not included`)
        }
    },
    loadExcludedAlleles,
    loadIncludedAlleles
]
