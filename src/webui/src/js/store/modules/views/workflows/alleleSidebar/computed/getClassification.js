import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import getClassification from '../../interpretation/computed/getClassification'

export default (alleles) => {
    return Compute(alleles, (alleles, get) => {
        const result = {}
        if (!alleles) {
            return result
        }
        for (let alleleId of Object.keys(alleles)) {
            // Cerebral tracks dependencies from getClassification as well
            result[alleleId] = get(
                getClassification(state`views.workflows.data.alleles.${alleleId}`)
            )
        }
        return result
    })
}
