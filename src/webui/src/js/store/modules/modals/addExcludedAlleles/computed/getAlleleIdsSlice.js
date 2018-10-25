import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default Compute(
    state`modals.addExcludedAlleles.geneAlleleIds`,
    state`modals.addExcludedAlleles.selectedPage`,
    state`modals.addExcludedAlleles.itemsPerPage`,
    (geneAlleleIds, selectedPage, itemsPerPage) => {
        const result = []
        if (!geneAlleleIds) {
            return result
        }
        return geneAlleleIds.slice((selectedPage - 1) * itemsPerPage, selectedPage * itemsPerPage)
    }
)
