/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state } from 'cerebral/tags'
import template from './alleleInfoPredictionOther.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('alleleInfoPredictionOther', {
    templateUrl: 'alleleInfoPredictionOther.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            allele: state`views.workflows.interpretation.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoPredictionOther',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    hasContent() {
                        return $ctrl.config.custom_annotation.prediction.some((group) => {
                            return (
                                $ctrl.allele &&
                                'prediction' in $ctrl.allele.annotation &&
                                group.key in $ctrl.allele.annotation.prediction
                            )
                        })
                    }
                })
            }
        ]
    )
})
