import thenBy from 'thenby'

import { state, props, string } from 'cerebral/tags'
import { Compute } from 'cerebral'

const FIELDS = ['count', 'num', 'hom', 'hemi', 'freq']

function getFields(allele) {
    return FIELDS.filter((i) => {
        // include hemi only for X and Y chromosomes
        if (i === 'hemi') {
            return allele.chromosome === 'X' || allele.chromosome === 'Y'
        }
        return true
    })
}

export function formatFreqValue(value, config) {
    const precision = config.frequencies.view.precision
    const scientificThreshold = config.frequencies.view.scientific_threshold
    if (isNaN(value)) {
        return 'N/A'
    } else if (value === 0) {
        return value
    } else if (value < Math.pow(10, -scientificThreshold)) {
        return value.toExponential(precision - scientificThreshold + 1)
    } else {
        return value.toFixed(precision)
    }
}

export function formatValue(freqData, name, freqType, config) {
    if (name === 'freq') {
        return formatFreqValue(freqData.freq[freqType], config)
    } else {
        return freqData[name][freqType]
    }
}

function getFilter(allele, group, freq_type) {
    if (
        allele.annotation.frequencies &&
        group in allele.annotation.frequencies &&
        'filter' in allele.annotation.frequencies[group] &&
        freq_type in allele.annotation.frequencies[group].filter
    ) {
        return allele.annotation.frequencies[group].filter[freq_type]
    }
}

function shouldShowIndications(allele, group, freqType, config) {
    if (
        group in allele.annotation.frequencies &&
        freqType in allele.annotation.frequencies[group].count
    ) {
        return (
            allele.annotation.frequencies[group].count[freqType] <
            config.frequencies.view.indications_threshold
        )
    }
}

export default function(allele, group) {
    return Compute(allele, group, state`app.config`, (allele, group, config) => {
        if (!allele) {
            return {}
        }
        const fields = getFields(allele)
        const data = {
            filter: [],
            indications: [],
            frequencies: [],
            fields: fields
        }

        if (!(group in config.frequencies.view.groups)) {
            return data
        }

        for (let freqType of config.frequencies.view.groups[group]) {
            //
            // Frequency data
            //
            if (group in allele.annotation.frequencies) {
                let freqDataForGroup = allele.annotation.frequencies[group]

                const container = {
                    name: freqType
                }

                for (let field of fields) {
                    if (field in freqDataForGroup && freqType in freqDataForGroup[field]) {
                        container[field] = formatValue(freqDataForGroup, field, freqType, config)
                    }
                }
                data.frequencies.push(container)
            }

            // rename labels:
            let translations
            switch (group) {
                case 'ExAC':
                    translations = config.frequencies.view.ExAC
                    break
                case 'GNOMAD_EXOMES':
                    translations = config.frequencies.view.GNOMAD_EXOMES
                    break
                case 'GNOMAD_GENOMES':
                    translations = config.frequencies.view.GNOMAD_GENOMES
                    break
            }

            if (translations) {
                data.frequencies.map((f) => {
                    if (f.name in translations) {
                        f.name = translations[f.name]
                    }
                    return f
                })
            }
            data.frequencies = data.frequencies.sort(thenBy((a) => a.name))

            //
            // Filter
            //
            const filterResult = getFilter(allele, group, freqType)
            if (filterResult) {
                data.filter = data.filter.concat(filterResult)
            }

            //
            // Indications
            //
            if (
                group in allele.annotation.frequencies &&
                'indications' in allele.annotation.frequencies[group] &&
                freqType in allele.annotation.frequencies[group].indications
            ) {
                let indications = Object.entries(
                    allele.annotation.frequencies[group].indications[freqType]
                )
                    .map((e) => {
                        return { name: e[0], value: e[1] }
                    })
                    .sort(thenBy((x) => x.name))
                if (shouldShowIndications(allele, group, freqType, config)) {
                    data.indications.push({
                        name: freqType,
                        indications: indications
                    })
                }
            }
        }
        return data
    })
}
