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

        this.selected_excluded = null;
    }

    getIncludedAlleles() {
        let included = this.alleles.filter(allele => {
            let allele_state = this.getAlleleState(allele);
            if (allele_state &&
                'report' in allele_state &&
                'included' in allele_state.report) {
                return allele_state.report.included;
            }
            return false;
        });
        included.sort((a, b) => {
            let ac = this.getClassification(a);
            let bc = this.getClassification(b);
            let aci = this.config.classification.options.findIndex(elem => {
                return elem.value === ac;
            });
            let bci = this.config.classification.options.findIndex(elem => {
                return elem.value === bc;
            });
            return bci - aci;
        });
        return included;
    }

    getExcludedAlleles() {
        return this.alleles.filter(allele => {
            let allele_state = this.state.allele.find(al => al.allele_id === allele.id);
            if (allele_state &&
                'report' in allele_state &&
                'included' in allele_state.report) {
                return !allele_state.report.included;
            }
            return true;
        });
    }

    getIncludedNeedsVerification() {
        return this.getIncludedAlleles().filter(al => {
            return al.annotation.quality.needs_verification;
        });
    }

    includeSelectedExcluded() {
        if (this.selected_excluded) {
            let allele_state = this.getAlleleState(this.selected_excluded);
            if (!('report' in allele_state)) {
                allele_state.report = {};
            };
            allele_state.report.included = true;
        }
        this.selected_excluded = null;
    }

    getAlleleState(allele) {
        return this.state.allele.find(al => al.allele_id === allele.id);
    }

    getClassification(allele) {
        let allele_state = this.getAlleleState(allele);
        if ('alleleassessment' in allele_state &&
            'classification' in allele_state.alleleassessment) {
            return allele_state.alleleassessment.classification;
        }
    }

    formatHGVS(allele) {
        let hgvs = '';
        for (let t of allele.annotation.filtered) {
            hgvs += `${t.Transcript}.${t.Transcript_version}(${t.SYMBOL}):`;
            let part = t.HGVSc_short.split("c.", 2)[1]; // remove 'c.'
            if (allele.genotype.homozygous) {
                hgvs += `c.[${part}];[(${part})]`; // c.[76A>C];[(76A>C)]
            }
            else {
                hgvs += `c.[${part}];[=]`; // c.[76A>C];[=]
            }
            let classification = this.getClassification(allele);
            if (classification) {
                hgvs += ` ${this.config.report.classification_text[classification]}`;
            }
            hgvs += `\n${t.HGVSc_short}`;
            if (t.HGVSp_short) {
                hgvs += ` ${t.HGVSp_short}`;
            }
            hgvs += '\n\n';

        }
        hgvs += ``;
        return hgvs;
    }

}
