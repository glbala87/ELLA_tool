/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-dbsnp',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoDbsnp.ngtmpl.html'
})
@Inject()
export class AlleleInfoDbsnp {

    constructor() {}

    getUrl(dbsnp) {
        return `http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=${dbsnp}`;
    }

    hasContent() {
        return this.allele.annotation.filtered.some(t => 'Existing_variation' in t);
    }

}
