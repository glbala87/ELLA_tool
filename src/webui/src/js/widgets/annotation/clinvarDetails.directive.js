import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import getClinvarAnnotation from '../../store/common/computes/getClinvarAnnotation'
import template from './clinvarDetails.ngtmpl.html' // eslint-disable-line no-unused-vars

const NUM_STARS = {
    'no assertion criteria provided': 0,
    'no assertion provided': 0,
    'criteria provided, conflicting interpretations': 1,
    'criteria provided, single submitter': 1,
    'criteria provided, multiple submitters, no conflicts': 2,
    'reviewed by expert panel': 3,
    'practice guideline': 4
}

app.component('clinvarDetails', {
    templateUrl: 'clinvarDetails.ngtmpl.html',
    bindings: {
        source: '@',
        title: '@',
        allelePath: '<',
        configIdx: '@'
    },
    controller: connect(
        {
            data: state`${props`allelePath`}.annotation.${props`source`}`,
            viewConfig: state`app.config.annotation.view.${props`configIdx`}.config`
        },
        'ClinvarDetails',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    getStarClass(i) {
                        let numStars = NUM_STARS[$ctrl.data.variant_description]
                        if (numStars === undefined) {
                            return 'unavailable'
                        }

                        return i < numStars ? 'filled' : ''
                    }
                })
            }
        ]
    )
})
