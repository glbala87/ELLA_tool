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
        readOnly: '=?'
    }

})
@Inject(
    'Config',
    '$sce'
)
export class ReportCardController {


    constructor(Config,
                $sce) {
        this.config = Config.getConfig();
        this.sce = $sce;
        this.selected_excluded = null;
    }

    getAlleleState(allele) {
        return this.state.allele[allele.id];
    }

    getAlleleReport(allele) {
        return AlleleStateHelper.getAlleleReport(allele, this.getAlleleState(allele));
    }


    getClassification(allele) {
        return AlleleStateHelper.getClassification(allele, this.getAlleleState(allele));
    }

    getAlleleReportComment(allele) {
        return this.sce.trustAsHtml(this.getAlleleReport(allele).evaluation.comment);
    }

    getAlleles() {
        this.alleles.sort(
            firstBy(a => {
                let classification = AlleleStateHelper.getClassification(a, this.getAlleleState(a));
                return this.config.classification.options.findIndex(o => o.value === classification);
            }, -1)
            .thenBy(a => a.annotation.filtered[0].symbol)
            .thenBy(a => a.annotation.filtered[0].HGVSc_short)
        )
        return this.alleles;
    }

    formatHGVS(allele) {
        let hgvs = '';
        for (let t of allele.annotation.filtered) {
            hgvs += `${t.transcript}(${t.symbol}):`;
            let part = t.HGVSc_short.split("c.", 2)[1]; // remove 'c.'
            if (allele.samples[0].genotype.homozygous) {
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
