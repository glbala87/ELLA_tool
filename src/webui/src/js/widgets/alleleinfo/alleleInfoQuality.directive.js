/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-quality',
    scope: {
        allele: '=',
        cbOptions: '='
    },
    templateUrl: 'ngtmpl/alleleInfoQuality.ngtmpl.html'
})
@Inject()
export class AlleleInfoQuality {

    constructor() {
        this.cbOptions.title = 'Quality';
    }

    getVerificationText() {
        return this.allele.annotation.quality.needs_verification ? 'Yes' : 'No';
    }
}
