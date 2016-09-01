/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-dbsnp',
    scope: {
        allele: '=',
        cbOptions: '='
    },
    templateUrl: 'ngtmpl/alleleInfoDbsnp.ngtmpl.html'
})
@Inject()
export class AlleleInfoDbsnp {

    constructor() {

        this.checkForContent();

        this.cbOptions.title = "dbSNP";
    }

    checkForContent() {
        if (!this.hasContent()) {
            this.cbOptions.disabled = true;
            this.cbOptions.collapsed = true;
        };
    }

    getUrl(dbsnp) {
        return `http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=${dbsnp}`;
    }

    hasContent() {
        return this.allele.annotation.filtered.some(t => 'Existing_variation' in t &&
                                                          t.Existing_variation.length);
    }

}
