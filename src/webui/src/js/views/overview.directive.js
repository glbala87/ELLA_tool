/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'overview',
    templateUrl: 'ngtmpl/overview.ngtmpl.html',
    scope: {
        selectedView: '='
    }
})
@Inject('SearchResource')
export class MainController {
    constructor(SearchResource) {
        this.searchResource = SearchResource;
        this.search = {
            results: null,
            query: ''
        }
    }

    updateSearch() {
        if (this.search.search_query && this.search.search_query.length > 2) {
            SearchResource.get(this.search.search_query).then(r => {
                this.search.results = r;
            });
        }
        else {
            this.search.results = null;
        }
    }

    hasSearchResults() {
        return this.search.results || false;
    }

    setView(view) {
        this.selectedView = view;
    }

    isActive(view) {
        return this.selectedView === view;
    }

}
