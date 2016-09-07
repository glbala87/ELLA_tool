/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-dbsnp',
    scope: {
        allele: '=',
        collapsed: '=?'
    },
    templateUrl: 'ngtmpl/alleleInfoDbsnp.ngtmpl.html'
})
@Inject()
export class AlleleInfoDbsnp {

    constructor() {
        if (!this.hasContent()) {
            this.collapsed = true;
        }
    }

    getUrl(dbsnp) {
        return `http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=${dbsnp}`;
    }

    hasContent() {
        return this.allele.annotation.filtered.some(t => 'Existing_variation' in t &&
                                                          t.Existing_variation.length);
    }

}
