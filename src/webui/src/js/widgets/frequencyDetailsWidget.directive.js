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
        this.precision = 4;
    }


}
