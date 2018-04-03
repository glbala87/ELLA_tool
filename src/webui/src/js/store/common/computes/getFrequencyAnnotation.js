import { state, props, string } from 'cerebral/tags'
import { Compute } from 'cerebral'

/*

constructor(Config, $scope) {
        this.config = Config.getConfig();
        this.precision = this.config.frequencies.view.precision;
        this.scientific_threshold = this.config.frequencies.view.scientific_threshold;
        this.frequencies = [];
        this.fields = ['count', 'num', 'hom', 'hemi', 'freq'].filter(i => {
             // include hemi only for X and Y chromosomes
            if (i === 'hemi') {
                return this.allele.chromosome === 'X' ||
                       this.allele.chromosome === 'Y'
            }
            return true
        })
        $scope.$watch(() => this.allele, () => {this.setFrequencies()});
    }

    getFreqTypes() {
        return this.config.frequencies.view.groups[this.group];
    }

    setFrequencies() {
        this.frequencies = [];
        let freq_types = this.getFreqTypes();
        if (!freq_types) {
            return;
        }

        for (let freq_type of freq_types) {
            if (this.group in this.allele.annotation.frequencies) {
                let annotation_data_for_group = this.allele.annotation.frequencies[this.group];

                // Filter based on frequencies group names from config, since we
                // might not want to show everything
                let data_container = {
                    name: freq_type,
                    freq: annotation_data_for_group.freq[freq_type] // ? annotation_data_for_group.freq[freq_type] : "0"
                }

                for (let field of this.fields) {
                    if (hasDataAtKey(annotation_data_for_group, field, freq_type)) {
                        data_container[field] = annotation_data_for_group[field][freq_type];
                    }
                }
                this.frequencies.push(data_container);
            }
        }

        // rename labels:
        var translations;
        switch (this.group) {
            case 'ExAC':
                translations = this.config.frequencies.view.ExAC;
                break;
            case 'GNOMAD_EXOMES':
                translations = this.config.frequencies.view.GNOMAD_EXOMES;
                break;
            case 'GNOMAD_GENOMES':
                translations = this.config.frequencies.view.GNOMAD_GENOMES;
                break;
        }

         if (translations) {
          this.frequencies.forEach( (e) => { e.name = translations[e.name] } );
        }
    }

    getFilter(freq_type) {
        if (this.allele.annotation.frequencies &&
            this.group in this.allele.annotation.frequencies &&
            'filter' in this.allele.annotation.frequencies[this.group] &&
            freq_type in this.allele.annotation.frequencies[this.group].filter) {
                return this.allele.annotation.frequencies[this.group].filter[freq_type]
            }
    }

    isFilterFail(freq_type) {
        let filter = this.getFilter(freq_type);
        if (filter) {
            return filter.length == 1 && filter[0] !== 'PASS';
        }
        return false;
    }

    formatValue(freq_data, name) {
      if(name === "freq") {
        return this.getFreqValue(freq_data)
      } else {
        return freq_data[name];
      }
    }


    getFreqValue(freq_data) {
        let value = parseFloat(freq_data.freq);
        if (isNaN(value)) {
            return "N/A"
        } else if (value === 0) {
            return value;
        } else if (value < Math.pow(10, -this.scientific_threshold)) {
            return value.toExponential(this.precision-this.scientific_threshold+1)
        } else {
            return value.toFixed(this.precision);
        }
    }

    showIndications(freq_type) {
        if (this.group in this.allele.annotation.frequencies &&
            'indications' in this.allele.annotation.frequencies[this.group] &&
            freq_type in this.allele.annotation.frequencies[this.group].indications) {
                return this.allele.annotation.frequencies[this.group].count[freq_type] <
                       this.config.frequencies.view.indications_threshold;
        }
    }
*/

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

function getFreqValue(freqData, freqType, config) {
    const precision = config.frequencies.view.precision
    const scientificThreshold = config.frequencies.view.scientific_threshold
    let value = parseFloat(freqData.freq[freqType])
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

function formatValue(freqData, name, freqType, config) {
    if (name === 'freq') {
        return getFreqValue(freqData, freqType, config)
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

function isFilterFail(filter) {
    if (filter) {
        return filter.length == 1 && filter[0] !== 'PASS'
    }
    return false
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
            data.frequencies = data.frequencies.sort(firstBy((a) => a.name))

            //
            // Filter
            //
            const filterResult = getFilter(allele, group, freqType)
            if (filterResult && isFilterFail(filterResult)) {
                data.filter.push({
                    name: freqType,
                    filter: filterResult
                })
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
                    .sort(firstBy((x) => x.name))
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
