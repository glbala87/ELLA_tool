import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default function(allele) {
    return Compute(allele, state`app.config`, (allele, config) => {
        if (!allele || !allele.allele_assessment) {
            return false
        }

        const classification = allele.allele_assessment.classification
        // Find classification configuration from config
        const option = config.classification.options.find(o => o.value === classification)
        if (option === undefined) {
            throw Error(`Classification ${classification} not found in configuration.`)
        }
        if ('outdated_after_days' in option) {
            return (
                allele.allele_assessment.seconds_since_update / (3600 * 24) >=
                option.outdated_after_days
            )
        }
        return false
    })
}
