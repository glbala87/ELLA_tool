import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('search', {
    templateUrl: 'ngtmpl/searchModule.ngtmpl.html',
    controller: connect(
        {
            query: state`search.query`,
            options: state`search.options`,
            results: state`search.results`,
            queryChanged: signal`search.queryChanged`,
            optionsSearchChanged: signal`search.optionsSearchChanged`,
            showAnalysesClicked: signal`search.showAnalysesClicked`
        },
        'Search',
        [
            'cerebral',
            '$scope',
            (cerebral, $scope) => {
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
                    optionSelected: (key, newValue) => {
                        // A bit hackish due to angular-selector not
                        // updating model before calling function.
                        // Copy the query and merge in changes
                        $ctrl.queryChanged({
                            query: Object.assign({}, $ctrl.query, { [key]: newValue })
                        })
                    },
                    updateGeneOptions: (term) => {
                        // angular-selector needs a returned Promise, although
                        // we set the options="" ourselves
                        $ctrl.optionsSearchChanged({ options: { gene: term } })
                        return Promise.resolve([])
                    },
                    updateUserOptions: (term) => {
                        $ctrl.optionsSearchChanged({ options: { user: term } })
                        return Promise.resolve([])
                    }
                })
            }
        ]
    )
})
