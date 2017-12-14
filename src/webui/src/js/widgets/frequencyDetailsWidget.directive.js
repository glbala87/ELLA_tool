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
        this.exac_fields = ['count', 'num', 'hom', 'freq']

        $scope.$watch(() => this.allele, () => {this.setFrequencies()});
    }


    setFrequencies() {
        this.frequencies = [];
        let freq_types = this.config.frequencies.view.groups[this.group];
        if (!freq_types) {
            return;
        }

        for (let freq_type of freq_types) {
            if (this.group in this.allele.annotation.frequencies) {
                let annotation_data_for_group = this.allele.annotation.frequencies[this.group];
                // Filter based on frequencies group names from config, since we
                // might not want to show everything
                if (freq_type in annotation_data_for_group.freq) {
                    let data_container = {
                        name: freq_type,
                        freq: annotation_data_for_group.freq[freq_type]
                    }
                    // Add ExAC specific values
                    for (let category of ['het', 'hom', 'count', 'num']) {
                        if (hasDataAtKey(annotation_data_for_group, category, freq_type)) {
                            data_container[category] = annotation_data_for_group[category][freq_type];
                        }
                    }
                    this.frequencies.push(data_container);
                }
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

    isFilterFail() {
        if (this.allele.annotation.frequencies &&
            this.group in this.allele.annotation.frequencies &&
            'filter' in this.allele.annotation.frequencies[this.group] &&
            'status' in this.allele.annotation.frequencies[this.group].filter) {
                let status = this.allele.annotation.frequencies[this.group].filter.status
                return status.length == 1 && status[0] !== 'PASS'
            }
        return false;
    }

    getFilterStatus() {
        if (this.allele.annotation.frequencies &&
            this.group in this.allele.annotation.frequencies &&
            'filter' in this.allele.annotation.frequencies[this.group] &&
            'status' in this.allele.annotation.frequencies[this.group].filter) {
                return this.allele.annotation.frequencies[this.group].filter.status
            }
    }

    getExACHeaderName(name) { // like 'freq' -> 'Allele freq'
      return this.config.frequencies.view.ExAC_fields[name];
    }

    formatExACValue(freq_data, name) {
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
        if (value === 0) {
            return value;
        } else if (value < Math.pow(10, -this.scientific_threshold)) {
            return value.toExponential(this.precision-this.scientific_threshold+1)
        } else {
            return value.toFixed(this.precision);
        }
    }

    exacNames(freq_data) {
        return freq_data;
    }

    isExACOrGnomad() {
       return ['ExAC', 'GNOMAD_EXOMES', 'GNOMAD_GENOMES'].includes(this.group)
    }

    inDbIndicationThreshold() {
        if ('inDB' in this.allele.annotation.frequencies) {
            return this.allele.annotation.frequencies.inDB.count.AF <
                   this.config.frequencies.view.inDB.indications_threshold;
        }
    }

}
