import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { Compute } from 'cerebral'
import { state, props } from 'cerebral/tags'
import sortedAlleles from '../store/modules/views/overview/computed/sortedAlleles'
import template from './alleleList.ngtmpl.html'

// Uses prop to dynamically turn on/off sorting
const sortSwitch = (alleles, shouldSort) => {
    return Compute(alleles, shouldSort, (alleles, shouldSort, get) => {
        if (shouldSort === undefined || shouldSort) {
            // prop is optional, missing = true
            return get(sortedAlleles(alleles))
        } else {
            return alleles
        }
    })
}

app.component('alleleList', {
    templateUrl: 'alleleList.ngtmpl.html',
    bindings: {
        storePath: '<', // Path to alleles in store
        newTarget: '<', // Whether links should open in new target
        sort: '=?' // Whether to sort in client
    },
    controller: connect(
        {
            alleles: sortSwitch(state`${props`storePath`}`, props`sort`),
            config: state`app.config`
        },
        'AlleleList',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    getClassificationText(allele) {
                        if ('allele_assessment' in allele) {
                            return `CLASS ${allele.allele_assessment.classification}`
                        }
                        return 'NEW'
                    },
                    getPriorityText: (item) => {
                        if (item.priority > 1) {
                            return $ctrl.config.analysis.priority.display[item.priority]
                        }
                    },
                    getReviewComment: (item) => {
                        return item.review_comment
                    }
                })
            }
        ]
    )
})
