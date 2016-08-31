/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-consequence',
    scope: {
        allele: '=',
        cbOptions: '='
    },
    templateUrl: 'ngtmpl/alleleInfoConsequence.ngtmpl.html'
})
@Inject()
export class AlleleInfoVariantConsequence {

    constructor() {

        this.cbOptions.title = 'Consequence';
        this.cbOptions.url = this.allele.getEnsemblUrl();
    }

}
