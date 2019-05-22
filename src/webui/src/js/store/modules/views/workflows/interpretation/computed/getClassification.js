import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getAlleleState from './getAlleleState'
import isAlleleAssessmentOutdated from '../../../../../common/computes/isAlleleAssessmentOutdated'

export default function getClassification(allele) {
    return Compute(allele, state`app.config`, (allele, config, get) => {
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
        result.existing = allele.allele_assessment ? allele.allele_assessment.classification : null

        // Allele might not be part of current workflows
        // interpretation state, e.g. if displaying a independant
        // allele from backend
        const alleleState = get(getAlleleState(allele.id))
        if (alleleState && alleleState.alleleassessment) {
            result.current = alleleState.alleleassessment.classification || null
            result.reused = alleleState.alleleassessment.reuse
            result.classification = result.reused ? result.existing : result.current
            result.outdated = get(isAlleleAssessmentOutdated(allele))
        } else {
            result.classification = result.existing
        }

        result.hasClassification = Boolean(result.classification)
        return result
    })
}
