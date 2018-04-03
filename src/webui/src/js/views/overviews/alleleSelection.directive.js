import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('alleleSelection', {
    templateUrl: 'ngtmpl/alleleSelection.ngtmpl.html',
    controller: connect(
        {
            alleles: state`views.overview.data.alleles`,
            finalized: state`views.overview.data.allelesFinalized`,
            state: state`views.overview.state.variants`,
            // FIXME: Missing on-finalized-changed signal
            collapseChanged: signal`views.overview.collapseChanged`
        },
        'AlleleSelection',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    collapseChangedWrapper(collapsed, name) {
                        $ctrl.collapseChanged({
                            section: 'variants',
                            name,
                            collapsed
                        })
                    }
                })
            }
        ]
    )
})
