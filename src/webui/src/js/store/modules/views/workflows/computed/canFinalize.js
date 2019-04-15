import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getAlleleState from '../interpretation/computed/getAlleleState'
import getClassification from '../interpretation/computed/getClassification'
import getSelectedInterpretation from './getSelectedInterpretation'

export default Compute(
    state`views.workflows.type`,
    state`views.workflows.interpretation.data.alleles`,
    state`app.config`,
    (type, alleles, config, get) => {
        const interpretation = get(getSelectedInterpretation)
        const result = {
            canFinalize: false,
            messages: []
        }
        if (!alleles || !interpretation) {
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

        if (interpretation.status !== 'Ongoing') {
            result.canFinalize = false
            result.messages.push('Interpretation is not Ongoing')
            return result
        }

        const metRequirements = {}

        // Workflow status requirement
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

        // Classification related requirements
        if (Object.values(alleles).length === 0 || finalizeRequirementsConfig.allow_unclassified) {
            metRequirements.classifications = true
        } else {
            // All alleles that are not exempted in the config needs a valid
            // (not outdated) classification before finalization
            let notRelevantAlleleIds = []
            let technicalAlleleIds = []

            if (finalizeRequirementsConfig.allow_notrelevant) {
                notRelevantAlleleIds = Object.values(alleles)
                    .filter((allele) => {
                        const alleleState = get(getAlleleState(allele.id))
                        return alleleState.analysis.notrelevant || false
                    })
                    .map((a) => a.id)
            }

            if (finalizeRequirementsConfig.allow_technical) {
                technicalAlleleIds = Object.values(alleles)
                    .filter((allele) => {
                        const alleleState = get(getAlleleState(allele.id))
                        return alleleState.analysis.verification === 'technical'
                    })
                    .map((a) => a.id)
            }

            const allelesRequiresClassification = Object.values(alleles).filter(
                (a) => !notRelevantAlleleIds.includes(a.id) && !technicalAlleleIds.includes(a.id)
            )
            // Check that remaining alleles have classification and
            // if reused, that they're not outdated
            const allelesMissingClassication = allelesRequiresClassification.filter((allele) => {
                const alleleState = get(getAlleleState(allele.id))
                if (!alleleState) {
                    throw Error(`Allele id ${allele.id} is not in interpretation state`)
                }
                const classification = get(
                    getClassification(
                        state`views.workflows.interpretation.data.alleles.${allele.id}`
                    )
                )
                return !(
                    classification.hasClassification &&
                    (classification.reused ? !classification.outdated : true)
                )
            })

            if (allelesMissingClassication.length) {
                metRequirements.classifications = false
                if (allelesMissingClassication.length > 3) {
                    result.messages.push(
                        `${allelesMissingClassication.length} variants are missing classifications.`
                    )
                } else {
                    const variantText = allelesMissingClassication
                        .map((a) => a.formatted.display)
                        .join(', ')
                    result.messages.push(
                        `Some variants are missing classifications: ${variantText}`
                    )
                }
            } else {
                metRequirements.classifications = true
            }
        }
        result.canFinalize = Object.values(metRequirements).every((v) => v)
        return result
    }
)
