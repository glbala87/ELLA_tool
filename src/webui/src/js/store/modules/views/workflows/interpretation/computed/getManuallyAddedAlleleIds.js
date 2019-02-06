import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(
    /*
    Returns manuallyAddedAlleles that are actually filtered out,
    and not among the non-filtered alleles.

    Allele ids can be manually included from a filter, and then the user
    might have changed to a filter where the allele id is not filtered anymore.

    We assume that manually added alleles are important, and therefore
    the allele id should still remain in manuallyAddedAlleles in case user
    switces back to the previous filter.
    */
    state`views.workflows.interpretation.state`,
    state`views.workflows.interpretation.data.filteredAlleleIds`,
    (interpretationState, filteredAlleleIds, get) => {
        if (
            !interpretationState ||
            !('manuallyAddedAlleles' in interpretationState) ||
            !filteredAlleleIds ||
            !filteredAlleleIds.excluded_allele_ids
        ) {
            return []
        }

        const stateManuallyAddedAlleles = interpretationState.manuallyAddedAlleles
        const alleleIds = filteredAlleleIds.allele_ids
        const allExcludedAlleleIds = []
        for (const excludedAlleleIds of Object.values(filteredAlleleIds.excluded_allele_ids)) {
            allExcludedAlleleIds.push(...excludedAlleleIds)
        }

        if (
            !stateManuallyAddedAlleles.every(
                (aId) => alleleIds.includes(aId) || allExcludedAlleleIds.includes(aId)
            )
        ) {
            throw Error(
                'manuallyIncludedAlleles includes allele ids not present in filteredAlleleIds. This should not be possible.'
            )
        }

        return stateManuallyAddedAlleles.filter((aId) => !alleleIds.includes(aId))
    }
)
