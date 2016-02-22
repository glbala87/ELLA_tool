/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';

@Service({
    serviceName: 'Search'
})
@Inject('SearchResource')
export class SearchService {

    /**
     * Service for managing the search state
     */
    constructor(SearchResource) {
        this.model = {
            query: ''
        };
        this.searchResource = SearchResource;
        this.results = null;
        this.error = null;
    }

    search(query) {
        this.query = query;
        this.updateSearch();
    }

    updateSearch() {
        if (this.model.query.length > 2) {
            this.searchResource.get(this.model.query).then(r => {
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

    /**
     * Allows external input fields to use this.query as model.
     */
    getModel() {
        return this.model;
    }

    clear() {
        this.model.query = '';
    }

    getResults() {
        return this.results;
    }

    getError() {
        return this.error;
    }

}
