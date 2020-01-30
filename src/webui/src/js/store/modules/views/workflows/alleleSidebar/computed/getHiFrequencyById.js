import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default function getHiFrequencyById(alleles, key) {
    return Compute(
        alleles,
        state`views.workflows.interpretation.data.filterConfig`,
        key,
        (alleles, currentFilterConfig) => {
            const result = {}
            if (!alleles) {
                return result
            }

            for (let [alleleId, allele] of Object.entries(alleles)) {
                let maxMeetsThresholdValue = null
                let maxValue = null
                const annotationFrequencies = allele.annotation.frequencies
                for (let { provider, population, numThreshold } of frequencyGroupsGenerator(
                    currentFilterConfig
                ))
                    if (
                        provider in annotationFrequencies &&
                        key in annotationFrequencies[provider] &&
                        population in annotationFrequencies[provider][key]
                    ) {
                        // For frequency, check that 'num' is higher than required in config
                        // If provider is not in config, assume it's good
                        // (since it would be in filtering)
                        let meetsNumThreshold = !(key === 'freq' && numThreshold)
                        if (key === 'freq' && numThreshold) {
                            meetsNumThreshold =
                                annotationFrequencies[provider]['num'][population] > numThreshold
                        }

                        const newValue = annotationFrequencies[provider][key][population]
                        if (newValue > maxValue || maxValue === null) {
                            maxValue = newValue
                        }
                        if (
                            meetsNumThreshold &&
                            (newValue > maxMeetsThresholdValue || maxMeetsThresholdValue === null)
                        ) {
                            maxMeetsThresholdValue = newValue
                        }
                    }
                result[alleleId] = {
                    maxMeetsThresholdValue,
                    maxValue
                }
            }
            return result
        }
    )
}

export const getHiFrequencyDefinition = Compute(
    state`views.workflows.interpretation.data.filterConfig`,
    (currentFilterConfig) => {
        return Array.from(frequencyGroupsGenerator(currentFilterConfig))
    }
)

function* frequencyGroupsGenerator(filterConfig) {
    // Iterate over provider, population, and num threshold in filterconfig
    let frequencyGroups = {}
    let frequencyNumThresholds = {}
    if (filterConfig) {
        // WARNING: Select first frequency filter. Not strictly correct when there are multiple frequency filters defined.
        const frequencyFilter = filterConfig.filterconfig.filters.find(
            (f) => f.name === 'frequency'
        )
        if (frequencyFilter) {
            frequencyGroups = frequencyFilter.config.groups || {}
            frequencyNumThresholds = frequencyFilter.config.num_thresholds || {}
        }
    }
    for (const providers of Object.values(frequencyGroups)) {
        for (const [provider, populations] of Object.entries(providers)) {
            for (const population of populations) {
                let numThreshold = null
                if (
                    provider in frequencyNumThresholds &&
                    population in frequencyNumThresholds[provider]
                ) {
                    numThreshold = frequencyNumThresholds[provider][population]
                }
                yield { provider, population, numThreshold }
            }
        }
    }
}
