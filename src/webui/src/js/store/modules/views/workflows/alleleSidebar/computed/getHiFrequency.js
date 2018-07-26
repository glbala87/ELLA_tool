import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import { formatValue } from '../../../../../common/computes/getFrequencyAnnotation'

export default (key) =>
    Compute(state`views.workflows.data.alleles`, state`app.config`, key, (alleles, config) => {
        const result = {}
        if (!alleles) {
            return result
        }
        const frequencyGroups = config.variant_criteria.frequencies.groups
        for (let [alleleId, allele] of Object.entries(alleles)) {
            let maxVal = null
            let maxFormatted = null
            const annotationFrequencies = allele.annotation.frequencies
            for (const providers of Object.values(frequencyGroups)) {
                for (const [provider, populations] of Object.entries(providers)) {
                    for (const population of populations) {
                        if (
                            provider in annotationFrequencies &&
                            population in annotationFrequencies[provider][key]
                        ) {
                            if (annotationFrequencies[provider][key][population] > maxVal) {
                                maxVal = annotationFrequencies[provider][key][population]
                                maxFormatted = formatValue(
                                    annotationFrequencies[provider],
                                    key,
                                    population,
                                    config
                                )
                            }
                        }
                    }
                }
            }
            result[alleleId] = maxFormatted
        }
        return result
    })
