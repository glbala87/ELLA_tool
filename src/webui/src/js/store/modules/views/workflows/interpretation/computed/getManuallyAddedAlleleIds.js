import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

const getManuallyAddedAlleleIds = Compute(
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
    (interpretationState, filteredAlleleIds, get) => {
        if (
            !interpretationState ||
            !('manuallyAddedAlleles' in interpretationState) ||
            !filteredAlleleIds ||
            !filteredAlleleIds.excluded_alleles_by_caller_type
        ) {
            return []
        }

        const stateManuallyAddedAlleles = interpretationState.manuallyAddedAlleles
        const alleleIds = filteredAlleleIds.allele_ids
        let allExcludedAlleleIds = []

        for (let k of Object.keys(filteredAlleleIds.excluded_alleles_by_caller_type)) {
            for (const excludedAlleleIds of Object.values(
                filteredAlleleIds.excluded_alleles_by_caller_type[k]
            )) {
                allExcludedAlleleIds = allExcludedAlleleIds.concat(excludedAlleleIds)
            }
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

const getManuallyAddedAlleleIdsByCallerType = Compute(
    getManuallyAddedAlleleIds,
    state`views.workflows.alleleSidebar.callerTypeSelected`,
    state`views.workflows.interpretation.data.alleles`,
    (manuallyAddedAlleleIds, callerTypeSelected, alleles) => {
        if (!alleles) {
            return []
        }
        return Object.values(alleles)
            .filter(
                (a) => a.caller_type === callerTypeSelected && manuallyAddedAlleleIds.includes(a.id)
            )
            .map((a) => a.id)
    }
)

export { getManuallyAddedAlleleIds, getManuallyAddedAlleleIdsByCallerType }
