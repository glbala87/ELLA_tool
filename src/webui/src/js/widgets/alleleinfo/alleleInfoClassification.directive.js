/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import template from './alleleInfoClassification.ngtmpl.html'

app.component('alleleInfoClassification', {
    templateUrl: 'alleleInfoClassification.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            allele: state`views.workflows.interpretation.data.alleles.${state`views.workflows.selectedAllele`}`,
            readOnly: isReadOnly,
            showAlleleAssessmentHistory: signal`views.workflows.modals.alleleAssessmentHistory.showAlleleAssessmentHistoryClicked`
        },
        'AlleleInfoClassification',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    getClassificationConfig() {
                        let aclass = $ctrl.allele.allele_assessment.classification
                        if (
                            'classification' in this.config &&
                            'options' in this.config.classification
                        ) {
                            return this.config.classification.options.find(
                                (o) => o.value === aclass
                            )
                        } else {
                            return {}
                        }
                    },

                    isOutdated() {
                        if (!$ctrl.allele.allele_assessment) {
                            return
                        }
                        return (
                            $ctrl.allele.allele_assessment.seconds_since_update / (3600 * 24) >=
                            $ctrl.getClassificationConfig().outdated_after_days
                        )
                    },

                    getClassName() {
                        if (!$ctrl.allele.allele_assessment) {
                            return ''
                        }
                        let classification_config = $ctrl.getClassificationConfig()
                        if ('name' in classification_config) {
                            return classification_config.name
                        }
                        return $ctrl.allele.allele_assessment.classification
                    }
                })
            }
        ]
    )
})
