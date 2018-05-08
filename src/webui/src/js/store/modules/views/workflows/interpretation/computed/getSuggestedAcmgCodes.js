import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import getAlleleAssessment from './getAlleleAssessment'

export default (alleleId) => {
    return Compute(alleleId, getAlleleAssessment(alleleId), (alleleId, alleleAssessment, get) => {
        if (!alleleAssessment) {
            return []
        }
        return alleleAssessment.evaluation.acmg.suggested.filter((c) => !c.code.startsWith('REQ'))
    })
}
