import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getManuallyAddedAlleleIds from '../interpretation/computed/getManuallyAddedAlleleIds'

export default Compute(
    state`views.workflows.interpretation.data.filteredAlleleIds.allele_ids`,
    getManuallyAddedAlleleIds,
    (alleleIds, manuallyAddedAlleleIds) => {
        if (!alleleIds) {
            return []
        }
        alleleIds = alleleIds.slice()
        if (manuallyAddedAlleleIds) {
            alleleIds = alleleIds.concat(manuallyAddedAlleleIds)
        }
        return alleleIds
    }
)
