'use strict'
/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import selectedSection from '../../store/modules/views/overview/computed/selectedSection'

app.component('analysisSelection', {
    templateUrl: 'ngtmpl/analysisSelection-new.ngtmpl.html',
    controller: connect(
        {
            analyses: state`views.overview.data.analyses`,
            finalized: state`views.overview.data.analysesFinalized`,
            state: state`views.overview.state.${selectedSection}`,
            selectedSection: selectedSection,
            finalizedPageChanged: signal`views.overview.finalizedPageChanged`,
            collapseChanged: signal`views.overview.collapseChanged`
        },
        'AnalysisSelection',
        [
            '$scope',
            $scope => {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    collapseChangedWrapper(collapsed, name) {
                        $ctrl.collapseChanged({
                            section: $ctrl.selectedSection,
                            name,
                            collapsed
                        })
                    }
                })
            }
        ]
    )
})

@Directive({
    selector: 'analysis-selection-old',
    templateUrl: 'ngtmpl/analysisSelection.ngtmpl.html',
    scope: {
        byFindings: '=?'
    }
})
@Inject('$scope', '$interval', 'OverviewResource', 'User')
class AnalysisSelectionController {
    constructor($scope, $interval, OverviewResource, User) {
        this.scope = $scope
        this.interval = $interval
        this.overviewResource = OverviewResource
        this.user = User
        this.overview = null
        this.finalized_page = 1
        this.finalized = null // {pagination: obj, data: array}
        this.ongoing_user = [] // Holds filtered list of ongoing alleles belonging to user
        this.ongoing_others = [] // Inverse of above list
        this._setup()
    }

    _setup() {
        this.loadOverview()
        this.pollOverview()
    }

    pollOverview() {
        let cancel = this.interval(() => this.loadOverview(), 60000)
        this.scope.$on('$destroy', () => this.interval.cancel(cancel))
    }

    loadOverview() {
        this.overviewResource.getAnalysesOverview(this.byFindings).then(data => {
            this.overview = data

            this.ongoing_user = this.overview.ongoing.filter(item => {
                return (
                    item.interpretations[item.interpretations.length - 1].user.id ===
                    this.user.getCurrentUserId()
                )
            })

            this.ongoing_others = this.overview.ongoing.filter(item => {
                return (
                    item.interpretations[item.interpretations.length - 1].user.id !==
                    this.user.getCurrentUserId()
                )
            })
        })

        this.finalizedPageChanged()
    }

    finalizedPageChanged() {
        this.overviewResource.getAnalysesFinalizedOverview(this.finalized_page).then(data => {
            this.finalized = data
            this.finalized_page = data.pagination.page
        })
    }
}

export default AnalysisSelectionController
