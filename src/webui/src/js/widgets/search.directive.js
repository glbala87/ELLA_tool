/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'

@Directive({
    selector: 'search',
    templateUrl: 'ngtmpl/search.ngtmpl.html'
})
@Inject('Search', '$timeout')
export class SearchController {
    constructor(Search, $timeout) {
        this.searchService = Search
        this.timeout = $timeout
        this.model = this.searchService.getModel()
    }

    clear() {
        this.searchService.clear()
    }

    updateSearch() {
        this.searchService.updateSearch()
        if (!this.model.query.length) {
        }
    }
}
