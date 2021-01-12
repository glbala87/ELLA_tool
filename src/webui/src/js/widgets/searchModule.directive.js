import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './searchModule.ngtmpl.html' // eslint-disable-line no-unused-vars

const TYPES = [
    {
        name: 'Variants',
        type: 'alleles'
    },
    {
        name: 'Analyses',
        type: 'analyses'
    }
]

app.component('search', {
    templateUrl: 'searchModule.ngtmpl.html',
    controller: connect(
        {
            query: state`search.query`,
            totalCount: state`search.totalCount`,
            options: state`search.options`,
            results: state`search.results`,
            limit: state`search.limit`,
            queryChanged: signal`search.queryChanged`,
            page: state`search.page`,
            pageChanged: signal`search.pageChanged`,
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
                    getSearchResultSummary: () => {
                        return `${TYPES.find((t) => t.type === $ctrl.query.type).name} (${
                            $ctrl.totalCount >= $ctrl.limit
                                ? 'showing first ' + $ctrl.totalCount
                                : $ctrl.totalCount
                        })`
                    },
                    getSearchTypes: () => {
                        return TYPES
                    },
                    optionSelected: (key, newValue) => {
                        // A bit hackish due to angular-selector not
                        // updating model before calling function.
                        // Copy the query and merge in changes

                        const newQuery = Object.assign({}, $ctrl.query, { [key]: newValue })
                        if (key != 'page') {
                            newQuery.page = 1
                        }
                        $ctrl.queryChanged({ query: newQuery })
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
