import { deepEquals } from '../../../../../../util'
import { prepareAlleleAssessmentModel } from '../../../../../common/helpers/alleleState'
import getAlleleState from '../computed/getAlleleState'

export default function autoReuseExistingAlleleassessments({ state, resolve }) {
    const alleles = state.get('views.workflows.interpretation.data.alleles')
    const checkReportAlleleIds = []
    const updatedAlleleAssessmentAlleleIds = []
    const defaultAlleleAssessmentModel = {}
    prepareAlleleAssessmentModel(defaultAlleleAssessmentModel)

    for (let [alleleId, allele] of Object.entries(alleles)) {
        if (!allele.allele_assessment) {
            continue
        }

        const alleleState = resolve.value(getAlleleState(alleleId))

        const alleleassessmentStateIsInital =
            deepEquals(alleleState.alleleassessment, defaultAlleleAssessmentModel) ||
            deepEquals(alleleState.alleleassessment, {})

        const hasNewAlleleAssessment =
            !('reuseCheckedId' in alleleState.alleleassessment) ||
            alleleState.alleleassessment.reuseCheckedId < allele.allele_assessment.id
        // Check if allele assessment has been updated, i.e. if the current state is not in its inital state
        // Need to check this to avoid toast messages for all classified alleles when opening an analysis for the first time
        const hasUpdatedAlleleAssessment = hasNewAlleleAssessment && !alleleassessmentStateIsInital

        const isReused = alleleState.alleleassessment.reuse

        if (hasNewAlleleAssessment || isReused) {
            const reusedAlleleAssessment = {
                allele_id: allele.id,
                reuse: true,
                reuseCheckedId: allele.allele_assessment.id
            }

            state.set(
                `views.workflows.interpretation.state.allele.${alleleId}.alleleassessment`,
                reusedAlleleAssessment
            )
        }

        if (hasNewAlleleAssessment) {
            checkReportAlleleIds.push(allele.id)
        }
        if (hasUpdatedAlleleAssessment) {
            updatedAlleleAssessmentAlleleIds.push(allele.id)
        }
    }
    return { checkReportAlleleIds, updatedAlleleAssessmentAlleleIds }
}
