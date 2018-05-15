import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import getClassification from '../interpretation/computed/getClassification'
import isAlleleAssessmentReused from '../interpretation/computed/isAlleleAssessmentReused'
import isAlleleAssessmentOutdated from '../../../../common/computes/isAlleleAssessmentOutdated'

export default Compute(
    state`views.workflows.type`,
    state`views.workflows.data.alleles`,
    state`views.workflows.interpretation.selected`,
    state`app.config`,
    (type, alleles, interpretation, config, get) => {
        if (!alleles) {
            return true
        }
        let inRequiredRound = true // Default is to omit test
        if (
            config.user.user_config.workflows &&
            type in config.user.user_config.workflows &&
            'finalize_required_workflow_status' in config.user.user_config.workflows[type] &&
            config.user.user_config.workflows[type].finalize_required_workflow_status.length
        ) {
            inRequiredRound = config.user.user_config.workflows[
                type
            ].finalize_required_workflow_status.includes(interpretation.workflow_status)
        }
        // Ensure that we have an interpretation with a state
        let allClassified = alleles.length === 0
        if (
            interpretation &&
            interpretation.status === 'Ongoing' &&
            'allele' in interpretation.state
        ) {
            // Check that all alleles
            // - have classification
            // - if reused, that they're not outdated
            allClassified = Object.entries(alleles).every((e) => {
                let [alleleId, allele] = e
                if (alleleId in interpretation.state.allele) {
                    const isReused = get(isAlleleAssessmentReused(alleleId))
                    const isOutdated = get(isAlleleAssessmentOutdated(allele))
                    let notReusedOutdated = true
                    if (isReused) {
                        notReusedOutdated = !isOutdated
                    }
                    const hasClassification = Boolean(get(getClassification(alleleId)))
                    return hasClassification && notReusedOutdated
                }
            })
        }

        return inRequiredRound && allClassified
    }
)