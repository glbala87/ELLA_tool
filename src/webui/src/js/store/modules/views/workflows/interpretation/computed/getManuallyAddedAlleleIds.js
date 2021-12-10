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
    switches back to the previous filter.
    */
    state`views.workflows.interpretation.state`,
    state`views.workflows.interpretation.data.filteredAlleleIds`,
    state`views.workflows.alleleSidebar.callerTypeSelected`,
    (interpretationState, filteredAlleleIds, callerTypeSelected, get) => {
        if (
            !interpretationState ||
            !('manuallyAddedAlleles' in interpretationState) ||
            Object.prototype.toString.call(interpretationState.manuallyAddedAlleles) ===
                '[object Array]' ||
            !filteredAlleleIds ||
            !filteredAlleleIds.excluded_alleles_by_caller_type ||
            !callerTypeSelected
        ) {
            return []
        }

        const stateManuallyAddedAlleles =
            interpretationState.manuallyAddedAlleles[callerTypeSelected]
        const alleleIds = filteredAlleleIds.allele_ids
        let allExcludedAlleleIds = []
        for (const excludedAlleleIds of Object.values(
            filteredAlleleIds.excluded_alleles_by_caller_type[callerTypeSelected]
        )) {
            allExcludedAlleleIds = allExcludedAlleleIds.concat(excludedAlleleIds)
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
