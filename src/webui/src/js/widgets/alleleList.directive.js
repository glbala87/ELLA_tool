import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { Compute } from 'cerebral'
import { state, props, signal } from 'cerebral/tags'
import sortedAlleles from '../store/modules/views/overview/computed/sortedAlleles'

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
    templateUrl: 'ngtmpl/alleleList.ngtmpl.html',
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
                    getEndAction: (interpretation) => {
                        let end_action = `${interpretation.workflow_status} ${
                            interpretation.finalized ? ' (Finalized) ' : ' '
                        }`
                        if (interpretation.user) {
                            return end_action + ' • '
                        } else {
                            return end_action
                        }
                    },
                    getPriorityText: (item) => {
                        if (item.highest_analysis_priority > 1) {
                            return $ctrl.config.analysis.priority.display[
                                item.highest_analysis_priority
                            ]
                        }
                    },
                    getReviewComment: (item) => {
                        if (item.interpretations.length) {
                            let last_interpretation =
                                item.interpretations[item.interpretations.length - 1]
                            if ('review_comment' in last_interpretation) {
                                return last_interpretation.review_comment
                            }
                        }
                    }
                })
            }
        ]
    )
})
