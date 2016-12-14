/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {AlleleStateHelper} from '../../model/allelestatehelper';

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
    'Config'
)
export class ReportCardController {


    constructor(Config,
                Allele,
                Analysis) {
        this.config = Config.getConfig();
        this.selected_excluded = null;
    }

    getAlleleState(allele) {
        return this.state.allele.find(al => al.allele_id === allele.id);
    }

    getAlleleReport(allele) {
        return AlleleStateHelper.getAlleleReport(allele, this.getAlleleState(allele));
    }


    getClassification(allele) {
        return AlleleStateHelper.getClassification(allele, this.getAlleleState(allele));
    }

    getAlleles() {
        this.alleles.sort(
            firstBy(a => {
                let classification = AlleleStateHelper.getClassification(a, this.getAlleleState(a));
                return this.config.classification.options.findIndex(o => o.value === classification);
            }, -1)
            .thenBy(a => a.annotation.filtered[0].SYMBOL)
            .thenBy(a => a.annotation.filtered[0].HGVSc_short)
        )
        return this.alleles;
    }

    getAnalysisTagOptions() {
        return this.config.analysis.tags;
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
