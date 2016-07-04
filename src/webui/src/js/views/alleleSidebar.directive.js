/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'allele-sidebar',
    templateUrl: 'ngtmpl/alleleSidebar.ngtmpl.html',
    scope: {
        alleles: '=',  // Allele options: { unclassified: [ {allele: Allele, alleleState: {...}, inactive: true ] }, classified: [ ... ] }
        selected: '=' // Selected Allele
    }
})
@Inject()
export class AlleleSidebarController {

    constructor() {
    }

    select(allele) {
        this.selected = allele;
    }
}
