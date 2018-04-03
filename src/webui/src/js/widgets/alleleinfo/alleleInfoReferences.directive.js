import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, string, signal } from 'cerebral/tags'
import getReferenceAnnotation from '../../store/modules/views/workflows/interpretation/computed/getReferenceAnnotation'

app.component('alleleInfoReferences', {
    bindings: {
        title: '@',
        type: '@'
    },
    templateUrl: 'ngtmpl/alleleInfoReferences.ngtmpl.html',
    controller: connect(
        {
            references: getReferenceAnnotation(
                props`type`,
                state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
                state`views.workflows.interpretation.selected`,
                state`views.workflows.data.references`
            ),
            showExcluded: state`views.workflows.interpretation.selected.user_state.allele.${state`views.workflows.selectedAllele`}.showExcludedReferences`
        },
        'AlleleInfoReferences',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    hasContent() {
                        if ($ctrl.references) {
                            return (
                                $ctrl.references[$ctrl.type].unpublished.length +
                                    $ctrl.references[$ctrl.type].published.length >
                                0
                            )
                        }
                        return false
                    }
                })
            }
        ]
    )
})
