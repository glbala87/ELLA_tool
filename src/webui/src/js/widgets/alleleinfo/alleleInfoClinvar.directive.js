/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-clinvar',
    scope: {
        allele: '=',
        collapsed: '=?'
    },
    templateUrl: 'ngtmpl/alleleInfoClinvar.ngtmpl.html'
})
@Inject('Config')
export class AlleleInfoClinvar {

    constructor(Config) {
        this.config = Config.getConfig();
        this.previous = {};
        this.maxstars = new Array(4);

        if (!this.hasContent()) {
            this.collapsed = true;
        }
    }

    formatClinvar() {
        let result = [];
        if (this.hasContent()) {
            for (let idx=0; idx<this.allele.annotation.external.CLINVAR.length; idx++) {
                let item = {};
                let rcv = this.allele.annotation.external.CLINVAR[idx].rcv;
                let sigtext = this.allele.annotation.external.CLINVAR[idx].clinical_significance_descr;
                let phenotypetext = this.allele.annotation.external.CLINVAR[idx].traitnames;
                let revtext = this.allele.annotation.external.CLINVAR[idx].clinical_significance_status;
                let revstatus = this.config.annotation.clinvar.clinical_significance_status[revtext];

                item["sigtext"] = sigtext === 'not provided' ? "No classification" : sigtext;
                item["phenotypetext"] = phenotypetext === 'not specified' ? "No phenotype" : phenotypetext;
                item["revstars"] = revstatus;
                item["revtext"] = revtext;
                item["rcv"] = rcv;

                result.push(item);
            }
        }
        return result;
    }

    hasContent() {
        return 'CLINVAR' in this.allele.annotation.external;
    }

    getRCVUrl(rcv) {
        return "https://www.ncbi.nlm.nih.gov/clinvar/" + rcv;
    }

    idempoClinvar() {
        // Force JSON-representation to be the equal-check
        let cur = this.formatClinvar();
        if (angular.toJson(this.previous) != angular.toJson(cur)) {
            this.previous = cur;
        }
        return this.previous;
    }
}
