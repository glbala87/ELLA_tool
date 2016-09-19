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
                let revstars = "";
                for (let j=0; j<revstatus; j++) {
                    revstars += ''; // This renders as a filled star in FontAwesome font
                }

                for (let j=0; j<4-revstatus; j++) {
                    revstars += ''; // This renders as an empty star in FontAwesome font
                }
                item["sigtext"] = sigtext;
                item["phenotypetext"] = phenotypetext;
                item["revstars"] = revstars;
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

    getUrl(rcv) {
        return "http://www.ncbi.nlm.nih.gov/clinvar/"+rcv;
    }
}
