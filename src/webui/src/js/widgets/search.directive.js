/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'search',
    templateUrl: 'ngtmpl/search.ngtmpl.html'
})
@Inject('SearchResource', 'AlleleAssessmentModal')
export class SearchController {

    constructor(SearchResource, AlleleAssessmentModal) {
        this.searchResource = SearchResource;
        this.alleleAssessmentModal = AlleleAssessmentModal;
        this.search_text = '';
        this.results = null;
        this.error = false;
        this.search_text = 'c.1444';
        this.updateSearch();
    }

    clear() {
        this.search_text = '';
    }

    updateSearch() {
        if (this.search_text.length > 2) {
            this.searchResource.get(this.search_text).then(r => {
                this.results = r;
                this.error = false;
            }).catch(e => {
                this.error = true;
            });
        }
        else {
            this.results = null;
            this.error = true;
        }
    }

    openAllele(allele) {
        this.alleleAssessmentModal.show(allele);
    }
}
