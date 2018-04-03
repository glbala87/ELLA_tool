/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, string, signal } from 'cerebral/tags'

app.component('alleleInfoPredictionOther', {
    templateUrl: 'ngtmpl/alleleInfoPredictionOther-new.ngtmpl.html',
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

@Directive({
    selector: 'allele-info-prediction-other-old',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoPredictionOther.ngtmpl.html'
})
@Inject('Config')
export class AlleleInfoPredictionOther {
    constructor(Config) {
        this.config = Config.getConfig()
    }

    hasContent() {
        return this.config.custom_annotation.prediction.some((group) => {
            return (
                'prediction' in this.allele.annotation &&
                group.key in this.allele.annotation.prediction
            )
        })
    }
}
