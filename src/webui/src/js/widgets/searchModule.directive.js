import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './searchModule.ngtmpl.html' // eslint-disable-line no-unused-vars

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
    templateUrl: 'searchModule.ngtmpl.html',
    controller: connect(
        {
            query: state`search.query`,
            options: state`search.options`,
            results: state`search.results`,
            queryChanged: signal`search.queryChanged`,
            optionsSearchChanged: signal`search.optionsSearchChanged`,
            showAnalysesForAlleleClicked: signal`search.modals.showAnalysesForAllele.showAnalysesForAlleleClicked`
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
