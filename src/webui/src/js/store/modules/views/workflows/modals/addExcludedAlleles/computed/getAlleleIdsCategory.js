import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(
    state`views.workflows.modals.addExcludedAlleles.excludedAlleleIds`,
    state`views.workflows.modals.addExcludedAlleles.category`,
    (excludedAlleleIds, category, get) => {
        const result = []
        if (!excludedAlleleIds) {
            return result
        }
        if (category === 'all') {
            return Object.values(excludedAlleleIds).reduce((baseArr, arr) => {
                return baseArr.concat(arr)
            }, [])
        } else {
            return excludedAlleleIds[category]
        }
    }
)
