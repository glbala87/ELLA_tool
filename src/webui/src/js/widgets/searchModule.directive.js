import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './searchModule.ngtmpl.html'

const TYPES = [
    {
        name: 'VARIANTS',
        type: 'alleles'
    },
    {
        name: 'ANALYSES',
        type: 'analyses'
    }
]

app.component('search', {
    template,
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
                    getSearchTypes: () => {
                        return TYPES
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
