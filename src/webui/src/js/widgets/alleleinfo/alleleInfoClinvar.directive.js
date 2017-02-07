/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-clinvar',
    scope: {
        allele: '='
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
        } else {
            this.revtext = this.allele.annotation.external.CLINVAR["variant_description"];
            this.revstars = this.config.annotation.clinvar.clinical_significance_status[this.revtext];
        }
    }

    formatClinvar() {
        let result = [];
        if (this.hasContent() && this.allele.annotation.external.CLINVAR) {
            for (let idx=0; idx<this.allele.annotation.external.CLINVAR["items"].length; idx++) {
                let item = {};
                let rcv = this.allele.annotation.external.CLINVAR["items"][idx].rcv;
                if (!rcv.startsWith("SCV")) {
                    continue;
                }


                let sigtext = this.allele.annotation.external.CLINVAR["items"][idx].clinical_significance_descr;
                let phenotypetext = this.allele.annotation.external.CLINVAR["items"][idx].traitnames;
                let submitter = this.allele.annotation.external.CLINVAR["items"][idx].submitter;
                let last_evaluated = this.allele.annotation.external.CLINVAR["items"][idx].last_evaluated;

                item["submitter"] = submitter === "" ? "Unknown" : submitter;
                item["last_evaluated"] = last_evaluated === "" ? "N/A" : last_evaluated;
                // item["sigtext"] = sigtext === 'not provided' ? "No classification" : sigtext;
                item["sigtext"] = sigtext === '' ? "No classification" : sigtext;
                // item["phenotypetext"] = phenotypetext === 'not specified' ? "No phenotype" : phenotypetext;
                item["phenotypetext"] = phenotypetext === '' ? "not specified" : phenotypetext;
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
