import { deepCopy } from '../../../../../util'
import { prepareAlleleAssessmentModel } from '../../../../common/helpers/alleleState'

export default function copyExistingAlleleAssessments({ state, props }) {
    const { copyExistingAlleleAssessmentAlleleIds } = props

    for (const alleleId of copyExistingAlleleAssessmentAlleleIds) {
        const allele = state.get(`views.workflows.data.alleles.${alleleId}`)
        if (!allele.allele_assessment) {
            throw Error(
                `Tried to copy existing alleleassessment for allele id ${alleleId}, which doesn't exist.`
            )
        }
        const existing = state.get(
            `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment`
        )
        if (existing.reuse) {
            throw Error(
                'Trying to copy in existing alleleassessment into reused state alleleassessment'
            )
        }
        const copiedAlleleAssessment = Object.assign({}, existing, {
            evaluation: deepCopy(allele.allele_assessment.evaluation),
            attachment_ids: deepCopy(allele.allele_assessment.attachment_ids),
            classification: allele.allele_assessment.classification
        })
        prepareAlleleAssessmentModel(copiedAlleleAssessment)
        state.set(
            `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment`,
            copiedAlleleAssessment
        )
    }
}
