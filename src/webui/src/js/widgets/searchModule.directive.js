/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'search-module',
    templateUrl: 'ngtmpl/searchModule.ngtmpl.html'
})
@Inject('$scope','Search', 'SearchResource', 'User', 'ShowAnalysesForAlleleModal')
export class SearchModuleController {

    constructor($scope, Search, SearchResource, User, ShowAnalysesForAlleleModal) {
        this.searchService = Search;
        this.searchResource = SearchResource;
        this.showAnalysesForAlleleModal = ShowAnalysesForAlleleModal;
        this.user = User;

        this.query = {
            freetext: undefined,
            gene: undefined,
            genepanel: undefined,
            user: undefined,
            filter: false,
        }

        // Options for dropdowns
        this.options = {
            gene: [],
            user: [],
            genepanel: []
        }

        $scope.$watch(
            () => this.query,
            () => {this.search()},
            true,
        )

    }

    updateGeneOptions(text) {
        return this.updateOptions({gene: text}).then(options => {
            if (text) {
                return options.gene
            }
            else {
                this.options.gene = []
                return this.options.gene
            }
        })
    }

    updateUserOptions(text) {
        return this.updateOptions({user: text}).then(options => {
            return options.user
        })
    }

    updateGenepanelOptions(text) {
        return this.updateOptions({genepanel: text}).then(options => {
            return options.genepanel
        })
    }

    updateOptions(query) {
        return this.searchResource.getOptions(query).then(result => {
            for (let key of Object.keys(result)) {
                this.options[key] = result[key]
            }
            return this.options
        })
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

    showAnalysesForAllele(allele) {
        this.showAnalysesForAlleleModal.show(allele);
    }

    getAlleleUrl(name, version, allele) {
        return `/variants/${allele.genome_reference}/${allele.chromosome}-${allele.vcf_pos}-${allele.vcf_ref}-${allele.vcf_alt}?gp_name=${name}&gp_version=${version}`;
    }
}
