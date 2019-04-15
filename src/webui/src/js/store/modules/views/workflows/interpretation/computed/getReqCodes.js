import { Compute } from 'cerebral';
import getAlleleAssessment from './getAlleleAssessment';


export default (alleleId) => {
    return Compute(alleleId, getAlleleAssessment(alleleId), (alleleId, alleleAssessment, get) => {
        let reqGroups = [] // array of req groups (arrays)
        if (!alleleAssessment) {
            return reqGroups
        }
        let reqs = alleleAssessment.evaluation.acmg.suggested.filter((c) =>
            c.code.startsWith('REQ')
        )
        for (let req of reqs) {
            let matchingGroup = reqGroups.find((rg) => rg.find((r) => r.code === req.code))
            if (matchingGroup) {
                matchingGroup.push(req)
            } else {
                reqGroups.push([req])
            }
        }
        return reqGroups
    })
}
