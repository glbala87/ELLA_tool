import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './alleleInfoSimilarAlleles.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('alleleInfoSimilarAlleles', {
    templateUrl: 'alleleInfoSimilarAlleles.ngtmpl.html',
    controller: connect(
        {
            similar_alleles: state`views.workflows.interpretation.data.similar.${state`views.workflows.selectedAllele`}`,
            config: state`app.config.similar_alleles`
        },
        'AlleleInfoSimilarAlleles',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    hasContent() {
                        return $ctrl.similar_alleles.length > 0
                    }
                })
            }
        ]
    )
})
