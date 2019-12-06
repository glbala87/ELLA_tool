import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getAlleleState from '../interpretation/computed/getAlleleState'
import getSelectedInterpretation from './getSelectedInterpretation'

export default function canFinalizeAllele(alleleId) {
    return Compute(
        alleleId,
        state`views.workflows.type`,
        state`views.workflows.interpretation.data.alleles`,
        state`app.config`,
        (alleleId, type, alleles, config, get) => {
            const interpretation = get(getSelectedInterpretation)

            const result = {
                canFinalize: false,
                messages: []
            }

            if (!alleleId || !alleles || !interpretation) {
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
                result.messages.push(
                    'Your user group is missing valid configuration. Contact support.'
                )
                return result
            }

            if (interpretation.status !== 'Ongoing') {
                result.canFinalize = false
                result.messages.push('Interpretation is not Ongoing')
                return result
            }

            const metRequirements = {}

            // Workflow status requirement
            if ('workflow_status' in finalizeRequirementsConfig) {
                if (
                    finalizeRequirementsConfig.workflow_status.includes(
                        interpretation.workflow_status
                    )
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

            // Classification related requirements
            const alleleState = get(getAlleleState(alleleId))
            if (!alleleState) {
                throw Error(`Allele id ${alleleId} is not in interpretation state`)
            }

            metRequirements.classification = Boolean(alleleState.alleleassessment.classification)
            if (!metRequirements.classification) {
                result.messages.push(
                    `Variant is missing classification. Please select a classification from the dropdown.`
                )
            }
            result.canFinalize = Object.values(metRequirements).every((v) => v)
            return result
        }
    )
}
