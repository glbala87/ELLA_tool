/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {AlleleStateHelper} from '../../model/allelestatehelper';

@Directive({
    selector: 'allele-info-vardb',
    scope: {
        allele: '=',
        alleleState: '=',
        readOnly: '=?'
    },
    templateUrl: 'ngtmpl/alleleInfoVardb.ngtmpl.html'
})
@Inject('Config')
export class AlleleInfoVardb {

    constructor(Config) {
        this.config = Config.getConfig();
    }

    isOutdated() {
        if (!this.allele.allele_assessment) {
            return;
        }
        return (this.allele.allele_assessment.secondsSinceUpdate / (3600 * 24)) >=
                this.config.classification.days_since_update;
    }

    getClassName() {
        if (!this.allele.allele_assessment) {
            return '';
        }
        let aclass = this.allele.allele_assessment.classification;
        try {
            return this.config.classification.options.find(o => o.value === aclass).name;
        }
        catch(err) {
            return aclass;
        }
    }

    hasContent() {
        return Boolean(this.allele.allele_assessment);
    }

    reset() {
        if (confirm("This will reset the classification, all ACMG codes and comments you've entered, for this variant, back to existing classification data. Proceed?")) {
            AlleleStateHelper.copyAlleleAssessmentToState(this.allele, this.alleleState, true);
            AlleleStateHelper.copyAlleleReportToState(this.allele, this.alleleState, true);
        }
    }
}
