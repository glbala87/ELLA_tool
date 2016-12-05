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
@Inject('Config')
export class FrequencyDetailsWidget {


    constructor(Config) {
        this.config = Config.getConfig();
        this.precision = this.config.frequencies.view.precision;
        this.frequencies = [];
        this.setFrequencies();
        this.exac_fields = ['count', 'num', 'hom', 'freq']
    }

    setFrequencies() {
        this.frequencies = [];
        let freqs = this.config.frequencies.view.groups[this.group];
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
        return parseFloat(freq_data[name]).toFixed(this.precision);
      } else {
        return freq_data[name];
      }
    }

    /**
     * Gets the value to display for the fiven freq data.
     * ExAC has more information, so we include that as well.
     * @return {string} Value to display for this freq data
     */
    getFreqValue(freq_data) {
        let value = parseFloat(freq_data.freq).toFixed(this.precision);
        return value;
    }

    exacNames(freq_data) {
        return freq_data;
    }

    isExAC() {
       return this.group === 'ExAC'
    }

    inDbIndicationThreshold() {
        if ('inDB' in this.allele.annotation.frequencies) {
            return this.allele.annotation.frequencies.inDB.num.AF <
                   this.config.frequencies.view.inDB.indications_threshold;
        }
    }

}
