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
        this.inDb = {
            indications: null,
            noMutInd: null
        }
        this.setFrequencies();
        this.setInDb();
    }

    setFrequencies() {
        this.frequencies = [];
        let freqs = this.config.frequencies.groups[this.group];
        for (let freq of freqs) {
            if (this.group in this.allele.annotation.frequencies) {
                let group_data = this.allele.annotation.frequencies[this.group];
                // Filter based on frequencies group names from config, since we
                // might not want to show everything
                if (freq in group_data) {
                    let freq_data = {
                        name: freq,
                        freq: group_data[freq]
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
    }

    /**
     * Gets the value to display for the fiven freq data.
     * ExAC has more information, so we include that as well.
     * @return {string} Value to display for this freq data
     */
    getFreqValue(freq_data) {
        let value = parseFloat(freq_data.freq).toFixed(this.precision);
        if ('hom' in freq_data) {
            value += ` (hom: ${freq_data['hom']} of ${freq_data['count']})`
        }
        return value;
    }

    setInDb() {
        if (this.group === 'inDB' &&
            'inDB' in this.allele.annotation.frequencies) {
            let group_data = this.allele.annotation.frequencies[this.group];
            if ('noMutInd' in group_data) {
                this.inDb.noMutInd = group_data.noMutInd;

                if(group_data.noMutInd < this.config.frequencies.inDB.noMutInd_threshold &&
                   'indications' in group_data) {
                    this.inDb.indications = group_data.indications;
                }
            }
        }
    }

}
