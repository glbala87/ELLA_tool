/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-external-other',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoExternalOther.ngtmpl.html'
})
@Inject('Config')
export class AlleleInfoExternalOther {

    constructor(Config) {
        this.config = Config.getConfig();
    }

}
