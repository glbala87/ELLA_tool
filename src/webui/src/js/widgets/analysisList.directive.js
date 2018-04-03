import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { Compute } from 'cerebral'
import { state, props, signal } from 'cerebral/tags'
import sortedAnalyses from '../store/modules/views/overview/computed/sortedAnalyses'

// Uses prop to dynamically turn on/off sorting
const sortSwitch = (analyses, shouldSort) => {
    return Compute(analyses, shouldSort, (analyses, shouldSort, get) => {
        if (shouldSort === undefined || shouldSort) {
            // prop is optional, missing = true
            return get(sortedAnalyses(analyses))
        } else {
            return analyses
        }
    })
}

app.component('analysisList', {
    templateUrl: 'ngtmpl/analysisList.ngtmpl.html',
    bindings: {
        storePath: '<', // Path to analyses in store
        newTarget: '<', // Whether links should open in new target
        sort: '=?' // Whether to sort in client
    },
    controller: connect(
        {
            analyses: sortSwitch(state`${props`storePath`}`, props`sort`),
            config: state`app.config`
        },
        'AnalysisList',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    isAnalysisDone: (analysis) => {
                        return (
                            analysis.interpretations.length &&
                            analysis.interpretations.every((i) => i.status === 'Done')
                        )
                    },
                    getPriorityText: (analysis) => {
                        if (analysis.priority > 1) {
                            return $ctrl.config.analysis.priority.display[analysis.priority]
                        }
                    },
                    getReviewComment: (analysis) => {
                        if (analysis.interpretations.length) {
                            let last_interpretation =
                                analysis.interpretations[analysis.interpretations.length - 1]
                            if ('review_comment' in last_interpretation) {
                                return last_interpretation.review_comment
                            }
                        }
                    },
                    getEndAction: (interpretation) => {
                        let OPTIONS = {
                            'Mark review': 'Marked for review',
                            Finalize: 'Finalized'
                        }
                        if (interpretation.end_action) {
                            return ' ' + OPTIONS[interpretation.end_action] + ' • '
                        }
                        if (interpretation.status === 'Ongoing') {
                            return ' Ongoing' + ' • '
                        }
                        return ''
                    }
                })
            }
        ]
    )
})
