/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'report-card',
    templateUrl: 'ngtmpl/reportcard.ngtmpl.html',
    scope: {
        analysis: '=',
        alleles: '=',
        references: '=',
        state: '=',
        userState: '=',
    }

})
@Inject(
    'Config',
    'Allele',
    'Analysis',
    'Interpretation'
)
export class ReportCardController {


    constructor(Config,
                Allele,
                Analysis,
                Interpretation) {
        this.config = Config.getConfig();
        this.alleleService = Allele;
        this.interpretationService = Interpretation;
        this.analysisService = Analysis;
    }

    getIncludedAlleles() {
        return this.alleles.filter(allele => {
            if ('report' in this.state.allele[allele.id] &&
                'included' in this.state.allele[allele.id].report) {
                return this.state.allele[allele.id].report.included;
            }
            return false;
        });
    }

    getExcludedAlleles() {
        return this.alleles.filter(allele => {
            if ('report' in this.state.allele[allele.id] &&
                'included' in this.state.allele[allele.id].report) {
                return !this.state.allele[allele.id].report.included;
            }
            return true;
        });
    }


    getAlleleState(allele) {
        return this.state.allele[allele.id];
    }

    getAlleleAssessment(allele) {
        this.getAlleleState(allele).alleleassessment;
    }


}
