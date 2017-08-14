/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'frequency-details',
    scope: {
        allele: '=',
        group: '@'
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
        let freqs = this.config.frequencies.view.groups[this.group];
        if (!freqs) {
            return;
        }

        for (let freq of freqs) {
            if (this.group in this.allele.annotation.frequencies) {
                let group_data = this.allele.annotation.frequencies[this.group];
                // Filter based on frequencies group names from config, since we
                // might not want to show everything
                if (freq in group_data.freq) {
                    let freq_data = {
                        name: freq,
                        freq: group_data.freq[freq]
                    }
                    // Add ExAC specific values
                    for (let group of ['het', 'hom', 'count', 'num']) {
                        if (group in group_data &&
                            freq in group_data[group]) {
                            freq_data[group] = group_data[group][freq];
                        }
                    }
                    this.frequencies.push(freq_data);
                }
            }
        }
        if(this.isExAC()) {
          this.frequencies.forEach( (e) => { e.name = this.config.frequencies.view.ExAC[e.name] } );
        }
    }

    getExACHeaderName(name) {
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

    isExAC() {
       return ['ExAC', 'GNOMAD_EXOMES', 'GNOMAD_GENOMES'].includes(this.group)
    }

    inDbIndicationThreshold() {
        if ('inDB' in this.allele.annotation.frequencies) {
            return this.allele.annotation.frequencies.inDB.count.AF <
                   this.config.frequencies.view.inDB.indications_threshold;
        }
    }

}
