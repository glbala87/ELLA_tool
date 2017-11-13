/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'search-module',
    templateUrl: 'ngtmpl/searchModule.ngtmpl.html'
})
@Inject('$scope','Search', 'GenepanelResource', 'User')
export class SearchModuleController {

    constructor($scope, Search, GenepanelResource, User) {
        this.searchService = Search;
        this.genepanelResource = GenepanelResource;
        this.userResource = User;

        this.query = {
            "freetext": undefined,
            "gene": undefined,
            "genepanel": undefined,
            "user": undefined,
            "filter": false,
        }

        $scope.$watch(
            () => {return this.query},
            () => {this.search()},
            true,
        )

        this.genepanels = [];
        this.users = [];
        this.genes = [];
        this.getGenepanels()
        this.getUsers()
    }

    clear() {
        this.searchService.clear();
        this.searchService.updateSearch();
    }

    getResults() {
        return this.searchService.getResults();
    }

    search() {
        this.searchService.search(this.query)
    }

    getGenepanels() {
        this.genepanelResource.getAll().then(genepanels => {
            let genes = genepanels.map( (gp) => {return gp.transcripts.map( (t) => {return t.gene.hugo_symbol})})
            genes = genes.concat(genepanels.map( (gp) => {return gp.phenotypes.map( (ph) => {return ph.gene.hugo_symbol})}))
            genes = [].concat.apply([], genes);
            this.genes = [...new Set(genes)].sort()

            this.genepanels = genepanels;
        });
    }

    getUsers() {
        this.userResource.getAll().then(users => {
            this.users = users;
        });
    }

    getAlleleUrl(name, version, allele) {
        return `/variants/${allele.genome_reference}/${allele.chromosome}-${allele.start_position}-${allele.open_end_position}-${allele.change_from}-${allele.change_to}?gp_name=${name}&gp_version=${version}`;
    }
}
