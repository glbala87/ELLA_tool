/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';
import {hasDataAtKey} from '../util';

@Directive({
    selector: 'frequency-details',
    scope: {
        allele: '=',
        group: '@' // e.g. name of data set, like ExAC or GNOMAD_EXOMES
    },
    templateUrl: 'ngtmpl/frequencyDetailsWidget.ngtmpl.html'
})
@Inject('Config', '$scope')
export class FrequencyDetailsWidget {


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

    /**
     * Gets the value to display for the given freq data.
     * ExAC has more information, so we include that as well.
     * @return {string} Value to display for this freq data
     */
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

}
