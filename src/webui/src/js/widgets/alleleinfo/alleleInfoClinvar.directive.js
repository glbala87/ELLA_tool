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
        if ('CLINVAR' in this.allele.annotation.external) {
            for (let idx=0; idx<this.allele.annotation.external.CLINVAR.length; idx++) {
                let sigtext = this.allele.annotation.external.CLINVAR[idx].clinical_significance_descr;
                let phenotypetext = this.allele.annotation.external.CLINVAR[idx].traitnames;
                let revtext = this.allele.annotation.external.CLINVAR[idx].clinical_significance_status;
                let revstatus = this.config.annotation.clinvar.clinical_significance_status[revtext];
                result.push(`${sigtext} - ${phenotypetext} - ${revstatus}`);
            }
        }
        return result;
    }

    hasContent() {
        return 'CLINVAR' in this.allele.annotation.external;
    }
}
