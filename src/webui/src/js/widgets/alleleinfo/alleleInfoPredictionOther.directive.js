/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, string, signal } from 'cerebral/tags'
import template from './alleleInfoPredictionOther.ngtmpl.html'

app.component('alleleInfoPredictionOther', {
    templateUrl: 'alleleInfoPredictionOther.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
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
