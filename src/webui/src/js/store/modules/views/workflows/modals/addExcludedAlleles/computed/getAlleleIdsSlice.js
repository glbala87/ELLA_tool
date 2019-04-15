import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(
    state`views.workflows.modals.addExcludedAlleles.geneAlleleIds`,
    state`views.workflows.modals.addExcludedAlleles.selectedPage`,
    state`views.workflows.modals.addExcludedAlleles.itemsPerPage`,
    (geneAlleleIds, selectedPage, itemsPerPage) => {
        const result = []
        if (!geneAlleleIds) {
            return result
        }
        return geneAlleleIds.slice((selectedPage - 1) * itemsPerPage, selectedPage * itemsPerPage)
    }
)
