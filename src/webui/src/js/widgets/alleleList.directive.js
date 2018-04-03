/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'

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
    templateUrl: 'ngtmpl/alleleList-new.ngtmpl.html',
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

@Directive({
    selector: 'allele-list-old',
    scope: {
        alleleItems: '=', // [{genepanel: {}, allele: Allele}, ...]
        newTarget: '=', // Open links in new target
        sort: '=?' // Whether to sort in client
    },
    templateUrl: 'ngtmpl/alleleList.ngtmpl.html'
})
@Inject(
    '$scope',
    'Config',
    'Sidebar',
    'User',
    'Analysis',
    'InterpretationResource',
    'InterpretationOverrideModal',
    'toastr'
)
class AlleleListWidget {
    constructor(
        $scope,
        Config,
        Sidebar,
        User,
        InterpretationResource,
        InterpretationOverrideModal,
        toastr
    ) {
        this.config = Config.getConfig()
        this.user = User
        this.interpretationResource = InterpretationResource
        this.interpretationOverrideModal = InterpretationOverrideModal
        this.toastr = toastr
        this.sort = 'sort' in this ? this.sort : true

        $scope.$watchCollection(() => this.alleleItems, () => this.sortItems())
        this.sorted_items = []
    }

    getEndAction(interpretation) {
        let end_action = `${interpretation.workflow_status} ${
            interpretation.finalized ? ' (Finalized) ' : ' '
        }`
        if (interpretation.user) {
            return end_action + ' • '
        } else {
            return end_action
        }
    }

    getClassificationText(allele) {
        if ('allele_assessment' in allele) {
            return `CLASS ${allele.allele_assessment.classification}`
        }
        return 'NEW'
    }

    sortItems() {
        if (!this.alleleItems) {
            return
        }
        this.sorted_items = this.alleleItems.slice()
        if (this.sort) {
            this.sorted_items.sort(
                firstBy((a) => a.highest_analysis_priority, -1)
                    .thenBy((a) => {
                        // Ignore seconds/milliseconds when sorting
                        let d = new Date(a.oldest_analysis)
                        d.setSeconds(0, 0)
                        return d.toISOString()
                    })
                    .thenBy((a) => a.allele.annotation.filtered[0].symbol)
                    .thenBy((a) => {
                        if (a.allele.annotation.filtered[0].strand > 0) {
                            return a.allele.start_position
                        }
                        return -a.allele.start_position
                    })
            )
        }
    }

    getPriorityText(item) {
        if (item.highest_analysis_priority > 1) {
            return this.config.analysis.priority.display[item.highest_analysis_priority]
        }
    }

    getReviewComment(item) {
        if (item.interpretations.length) {
            let last_interpretation = item.interpretations[item.interpretations.length - 1]
            if ('review_comment' in last_interpretation) {
                return last_interpretation.review_comment
            }
        }
    }

    getItemUrl(item) {
        return item.allele.getWorkflowUrl(item.genepanel)
    }
}

export default AlleleListWidget
