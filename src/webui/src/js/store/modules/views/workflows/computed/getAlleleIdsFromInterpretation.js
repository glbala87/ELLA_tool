import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(
    state`views.workflows.interpretation.data.filteredAlleleIds.allele_ids`,
    state`views.workflows.interpretation.state.manuallyAddedAlleles`,
    (alleleIds, manuallyAddedAlleles) => {
        if (!alleleIds) {
            return []
        }
        alleleIds = alleleIds.slice()
        if (manuallyAddedAlleles) {
            alleleIds = alleleIds.concat(manuallyAddedAlleles)
        }
        return alleleIds
    }
)
