/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-hgmd',
    scope: {
        allele: '=',
        cbOptions: '='
    },
    templateUrl: 'ngtmpl/alleleInfoHgmd.ngtmpl.html'
})
@Inject()
export class AlleleInfoHgmd {

    constructor() {

        this.cbOptions.title = 'HGMD Pro';
        this.cbOptions.url = this.allele.getHGMDUrl();
        this.checkForContent();
    }

    checkForContent() {
        if (!this.hasContent()) {
            this.cbOptions.disabled = true;
            this.cbOptions.collapsed = true;
        };
    }

    hasContent() {
        return 'HGMD' in this.allele.annotation.external;
    }
}
