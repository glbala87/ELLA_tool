import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import isAlleleAssessmentOutdated from '../../../../../common/computes/isAlleleAssessmentOutdated'
import getAlleleState from './getAlleleState'

export default function getClassification(alleleId, raw = false) {
    return Compute(
        state`views.workflows.data.alleles.${alleleId}`,
        state`app.config`,
        (allele, config, get) => {
            const result = {
                existing: null,
                current: null,
                reused: null,
                classification: null,
                outdated: null,
                hasClassification: false
            }
            if (!allele) {
                return result
            }
            const alleleState = get(getAlleleState(allele.id))
            if (!alleleState) {
                return result
            }
            const outdated = get(isAlleleAssessmentOutdated(allele))
            Object.assign(result, {
                existing: allele.allele_assessment ? allele.allele_assessment.classification : null,
                current: alleleState.alleleassessment.classification || null,
                reused: alleleState.alleleassessment.reuse || false,
                outdated,
                reviewed: false
            })
            result.classification = result.reused ? result.existing : result.current
            result.hasClassification = Boolean(result.classification)
            return result
        }
    )
}
