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
                if (freq in group_data) {
                    let freq_data = {
                        name: freq,
                        freq: group_data[freq]
                    }
                    this.frequencies.push(freq_data);
                }
            }
        }
    }

    setInDb() {
        if (this.group === 'inDB') {
            let group_data = this.allele.annotation.frequencies[this.group];
            if ('noMutInd' in group_data &&
                group_data.noMutInd < this.config.frequencies.inDB.noMutInd_threshold) {
                this.inDb.noMutInd = group_data.noMutInd;
            }
            if ('indications' in group_data) {
                this.inDb.indications = group_data.indications;
            }
        }
    }

}
