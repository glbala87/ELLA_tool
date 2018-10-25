import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default (alleles, key) => {
    return Compute(alleles, state`app.config`, key, (alleles, config) => {
        const result = {}
        if (!alleles) {
            return result
        }
        const frequencyGroups = config.variant_criteria.frequencies.groups
        const frequencyNumThresholds = config.variant_criteria.freq_num_thresholds || {}
        for (let [alleleId, allele] of Object.entries(alleles)) {
            let maxMeetsThresholdValue = null
            let maxValue = null
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
                            const newValue = annotationFrequencies[provider][key][population]
                            if (newValue > maxValue || maxValue === null) {
                                maxValue = newValue
                            }
                            if (
                                meetsNumThreshold &&
                                (newValue > maxMeetsThresholdValue ||
                                    maxMeetsThresholdValue === null)
                            ) {
                                maxMeetsThresholdValue = newValue
                            }
                        }
                    }
                }
            }
            result[alleleId] = {
                maxMeetsThresholdValue,
                maxValue
            }
        }
        return result
    })
}
