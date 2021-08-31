import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './alleleInfoExternalOther.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('alleleInfoExternalOther', {
    templateUrl: 'alleleInfoExternalOther.ngtmpl.html',
    bindings: {
        allelePath: '<'
    },
    controller: connect(
        {
            config: state`app.config`,
            allele: state`${props`allelePath`}`
        },
        'AlleleInfoExternalOther',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    hasContent() {
                        return $ctrl.config.custom_annotation.external.some((group) => {
                            return (
                                $ctrl.allele &&
                                'external' in $ctrl.allele.annotation &&
                                group.key in $ctrl.allele.annotation.external
                            )
                        })
                    }
                })
            }
        ]
    )
})
