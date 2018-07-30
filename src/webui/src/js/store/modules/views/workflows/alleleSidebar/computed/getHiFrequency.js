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
        const frequencyNumThresholds = config.variant_criteria.freq_num_thresholds || {}
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
                            // For frequency, check that 'num' is higher than required in config
                            // If provider is not in config, assume it's good
                            // (since it would be in filtering)
                            let meetsNumThreshold = !(
                                key === 'freq' && provider in frequencyNumThresholds
                            )
                            if (
                                key === 'freq' &&
                                provider in frequencyNumThresholds &&
                                population in frequencyNumThresholds[provider]
                            ) {
                                meetsNumThreshold =
                                    annotationFrequencies[provider]['num'][population] >
                                    frequencyNumThresholds[provider][population]
                            }

                            const isHigher =
                                annotationFrequencies[provider][key][population] > maxVal

                            if (meetsNumThreshold && isHigher) {
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
