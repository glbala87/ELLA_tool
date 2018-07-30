import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getAlleleAssessment from '../../interpretation/computed/getAlleleAssessment'

export default Compute(state`views.workflows.data.alleles`, (alleles, get) => {
    const result = {}
    if (!alleles) {
        return result
    }
    for (let [alleleId, allele] of Object.entries(alleles)) {
        const alleleAssessment = get(getAlleleAssessment(alleleId))
        if (alleleAssessment) {
            result[alleleId] = alleleAssessment
        }
    }
    return result
})
