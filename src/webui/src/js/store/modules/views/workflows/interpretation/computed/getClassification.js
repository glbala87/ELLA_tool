import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import getAlleleAssessment from './getAlleleAssessment'
import isAlleleAssessmentOutdated from '../../../../../common/computes/isAlleleAssessmentOutdated'

export default function getClassification(alleleId) {
    return Compute(
        state`views.workflows.data.alleles.${alleleId}`,
        state`app.config`,
        (allele, config, get) => {
            if (!allele) {
                return
            }

            const alleleAssessment = get(getAlleleAssessment(allele.id))
            const classification = alleleAssessment.classification
                ? alleleAssessment.classification
                : ''
            if (get(isAlleleAssessmentOutdated(allele))) {
                return `${classification}*`
            } else {
                return classification
            }
        }
    )
}
