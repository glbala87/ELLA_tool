/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'search',
    templateUrl: 'ngtmpl/search.ngtmpl.html'
})
@Inject('Search', 'AlleleAssessmentModal', '$timeout')
export class SearchController {

    constructor(Search, AlleleAssessmentModal, $timeout) {
        this.searchService = Search;
        this.alleleAssessmentModal = AlleleAssessmentModal;
        this.timeout = $timeout;
        this.model = this.searchService.getModel();
    }

    clear() {
        this.searchService.clear();
    }

    updateSearch() {
        this.searchService.updateSearch();
        if (!this.model.query.length) {

        }
    }

    openAllele(allele) {
        this.alleleAssessmentModal.show(allele);
    }
}
