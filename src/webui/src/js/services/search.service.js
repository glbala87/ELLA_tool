/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';
import {deepCopy} from "../util";

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
        this.model.query = this._formatSearchQuery(query);
        this.updateSearch();
    }

    _formatSearchQuery(query) {
        let _query = deepCopy(query)
        if (_query.genepanel) {
            _query.genepanel = [_query.genepanel.name, _query.genepanel.version];
        }
        if (_query.user) {
            _query.user = _query.user.id;
        }
        return _query

    }

    _isValidSearch() {
        let a = this.model.query.freetext === undefined;
        let b = this.model.query.gene === undefined;
        let c = this.model.query.user === undefined;
        let d = this.model.query.genepanel === undefined;

        if (!a && (b && c && d)) {
            return this.model.query.freetext.length > 2
        } else {
            return (!b || !c || !d);
        }
    }

    updateSearch() {
        if (this._isValidSearch()) {
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
