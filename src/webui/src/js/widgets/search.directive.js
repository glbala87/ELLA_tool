/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'
import template from './search.ngtmpl.html'

@Directive({
    selector: 'search',
    template
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
