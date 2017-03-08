/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'allele-assessment',
    scope: {
        allele: '=',
        alleleassessment: '=',
    },
    templateUrl: 'ngtmpl/alleleAssessment.ngtmpl.html'
})
@Inject('Config')
export class AlleleInfoVardb {

    constructor(Config, AlleleAssessmentHistoryModal) {
        this.config = Config.getConfig();
        console.log(this.alleleassessment);
    }

    getClassificationConfig() {
        let aclass = this.alleleassessment.classification;
        try {
            return this.config.classification.options.find(o => o.value === aclass);
        }
        catch(err) {
            return {}
        }
    }

    isOutdated() {
        if (!this.alleleassessment) {
            return;
        }
        return (this.alleleassessment.seconds_since_update / (3600 * 24)) >=
                this.getClassificationConfig().outdated_after_days;
    }

    getClassName() {
        if (!this.alleleassessment) {
            return '';
        }
        try {
            return this.getClassificationConfig().name;
        }
        catch(err) {
            return this.alleleassessment.classification;
        }
    }

}
