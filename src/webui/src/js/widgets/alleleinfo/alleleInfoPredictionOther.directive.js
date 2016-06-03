/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-prediction-other',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoPredictionOther.ngtmpl.html'
})
@Inject('Config')
export class AlleleInfoExternalOther {

    constructor(Config) {
        this.config = Config.getConfig();
    }

}
