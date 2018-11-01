import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import getClassification from '../interpretation/computed/getClassification'
import isAlleleAssessmentReused from '../interpretation/computed/isAlleleAssessmentReused'
import isAlleleAssessmentOutdated from '../../../../common/computes/isAlleleAssessmentOutdated'
import getAlleleAssessment from '../interpretation/computed/getAlleleAssessment'

export default Compute(
    state`views.workflows.type`,
    state`views.workflows.data.alleles`,
    state`views.workflows.interpretation.selected`,
    state`app.config`,
    (type, alleles, interpretation, config, get) => {
        const result = {
            canFinalize: false,
            messages: []
        }
        if (!alleles) {
            return result
        }
        let finalizeRequirementsConfig = null
        if (
            config.user.user_config.workflows &&
            type in config.user.user_config.workflows &&
            'finalize_requirements' in config.user.user_config.workflows[type]
        ) {
            finalizeRequirementsConfig =
                config.user.user_config.workflows[type].finalize_requirements
        }

        if (!finalizeRequirementsConfig) {
            result.canFinalize = false
            result.messages.push('Your user group is missing valid configuration. Contact support.')
            return result
        }

        const metRequirements = {}
        for (const key of Object.keys(finalizeRequirementsConfig)) {
            metRequirements[key] = false
        }

        if ('workflow_status' in finalizeRequirementsConfig) {
            if (
                finalizeRequirementsConfig.workflow_status.includes(interpretation.workflow_status)
            ) {
                metRequirements.workflow_status = true
            } else {
                metRequirements.workflow_status = false
                result.messages.push(
                    `You are not in one of the required workflow stages: ${finalizeRequirementsConfig.workflow_status.join(
                        ', '
                    )}`
                )
            }
        }

        if ('all_alleles_valid_classification' in finalizeRequirementsConfig) {
            if (finalizeRequirementsConfig.all_alleles_valid_classification) {
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
                            const alleleState = interpretation.state.allele[alleleId]
                            const isReused = get(isAlleleAssessmentReused(alleleId))
                            const isOutdated = get(isAlleleAssessmentOutdated(allele))
                            let notReusedOutdated = true
                            if (isReused) {
                                notReusedOutdated = !isOutdated
                            }
                            const hasClassification = get(getClassification(alleleId))
                                .hasClassification
                            const isTechnical = alleleState.analysis.verification === 'technical'
                            return (hasClassification && notReusedOutdated) || isTechnical
                        }
                    })
                }
                metRequirements.all_alleles_valid_classification = allClassified
            } else {
                metRequirements.all_alleles_valid_classification = true
            }
            if (!metRequirements.all_alleles_valid_classification) {
                result.messages.push('All variants need a valid (not outdated) classification')
            }
        }

        result.canFinalize = Object.values(metRequirements).every((v) => v)
        return result
    }
)
