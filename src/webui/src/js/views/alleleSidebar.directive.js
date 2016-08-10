/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';

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

    isSelected(allele) {
        return this.selected === allele;
    }

    getClassification(allele, allele_state) {
        return AlleleStateHelper.getClassification(allele, allele_state);
    }
}
