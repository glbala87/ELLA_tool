import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import getAlleleState from './getAlleleState'

export default alleleId => {
    return Compute(alleleId, getAlleleState(alleleId), (alleleId, alleleState, get) => {
        let reqGroups = [] // array of req groups (arrays)
        if (!alleleState) {
            return reqGroups
        }
        let reqs = alleleState.alleleassessment.evaluation.acmg.suggested.filter(c =>
            c.code.startsWith('REQ')
        )
        for (let req of reqs) {
            let matchingGroup = reqGroups.find(rg => rg.find(r => r.code === req.code))
            if (matchingGroup) {
                matchingGroup.push(req)
            } else {
                reqGroups.push([req])
            }
        }
        return reqGroups
    })
}
