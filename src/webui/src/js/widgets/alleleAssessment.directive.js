/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'

@Directive({
    selector: 'allele-assessment',
    scope: {
        allele: '=',
        alleleassessment: '=',
        allelereport: '=?',
        attachments: '=',
        summaryOnly: '=?'
    },
    templateUrl: 'ngtmpl/alleleAssessment.ngtmpl.html'
})
@Inject('Config')
export class AlleleInfoVardb {
    constructor(Config, AlleleAssessmentHistoryModal) {
        this.config = Config.getConfig()
    }

    getClassificationConfig() {
        let aclass = this.alleleassessment.classification
        if ('classification' in this.config && 'options' in this.config.classification) {
            return this.config.classification.options.find((o) => o.value === aclass)
        } else {
            return {}
        }
    }

    isOutdated() {
        if (!this.alleleassessment) {
            return
        }
        return (
            this.alleleassessment.seconds_since_update / (3600 * 24) >=
            this.getClassificationConfig().outdated_after_days
        )
    }

    getClassName() {
        if (!this.alleleassessment) {
            return ''
        }
        let classification_config = this.getClassificationConfig()
        if ('name' in classification_config) {
            return classification_config.name
        }
        return this.alleleassessment.classification
    }
}
