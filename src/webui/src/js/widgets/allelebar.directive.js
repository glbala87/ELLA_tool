/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'allelebar',
    scope: {
        allele: '=',
        genepanel: '=?',
    },
    templateUrl: 'ngtmpl/allelebar.ngtmpl.html'
})
@Inject('Config')
export class Allelebar {

    constructor(Config) {

        this.config = Config.getConfig();

    }

    getInheritanceCodes(geneSymbol) {
        return this.genepanel.getInheritanceCodes(geneSymbol);
    }

    phenotypesBy(geneSymbol) {
        return this.genepanel.phenotypesBy(geneSymbol);
    }

    getGenepanelValues(geneSymbol) {
        //  Cache calculation; assumes this card is associated with only one gene symbol
        if (! this.calculated_config && this.genepanel ) {
            this.calculated_config = this.genepanel.calculateGenepanelConfig(geneSymbol, this.config.variant_criteria.genepanel_config);
        }
        return this.calculated_config;
    }


}
