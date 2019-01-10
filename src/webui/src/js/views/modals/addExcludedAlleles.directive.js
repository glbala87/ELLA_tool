import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './addExcludedAlleles.ngtmpl.html'

const getGeneOptions = Compute(
    state`modals.addExcludedAlleles.data.alleleIdsByGene`,
    state`modals.addExcludedAlleles.categoryAlleleIds`,
    (alleleIdsByGene, categoryAlleleIds) => {
        if (!alleleIdsByGene || !categoryAlleleIds) {
            return
        }
        const alleleIds = new Set(categoryAlleleIds)
        return alleleIdsByGene
            .filter((a) => {
                return (
                    a.allele_ids.some((alleleId) => {
                        return alleleIds.has(alleleId)
                    }) && a.symbol
                )
            })
            .map((a) => a.symbol)
            .sort()
    }
)

const getMetrics = Compute(
    state`modals.addExcludedAlleles.excludedAlleleIds`,
    state`modals.addExcludedAlleles.geneAlleleIds`,
    (excludedAlleleIds, geneAlleleIds) => {
        const result = {}
        if (!excludedAlleleIds || !geneAlleleIds) {
            return result
        }
        result['all'] = 0
        Object.entries(excludedAlleleIds).reduce((result, keyValues) => {
            result['all'] += keyValues[1].length
            result[keyValues[0]] = keyValues[1].length
            return result
        }, result)
        result['current'] = geneAlleleIds.length
        return result
    }
)

const isToggled = Compute(
    state`modals.addExcludedAlleles.includedAlleleIds`,
    state`modals.addExcludedAlleles.viewAlleleIds`,
    (includedAlleleIds, viewAlleleIds) => {
        const result = {}
        if (!includedAlleleIds || !viewAlleleIds) {
            return result
        }
        for (const aId of includedAlleleIds) {
            result[aId] = true
        }
        for (const aId of viewAlleleIds) {
            result[aId] = false
        }
        return result
    }
)

app.component('addExcludedAlleles', {
    templateUrl: 'addExcludedAlleles.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            geneOptions: getGeneOptions,
            metrics: getMetrics,
            filterconfig: state`modals.addExcludedAlleles.filterconfig`,
            isToggled,
            genepanelPath: state`modals.addExcludedAlleles.genepanelPath`,
            geneAlleleIds: state`modals.addExcludedAlleles.geneAlleleIds`,
            alleleIds: state`modals.addExcludedAlleles.viewAlleleIds`,
            includedAlleleIds: state`modals.addExcludedAlleles.includedAlleleIds`,
            itemsPerPage: state`modals.addExcludedAlleles.itemsPerPage`,
            readOnly: state`modals.addExcludedAlleles.readOnly`,
            selectedPage: state`modals.addExcludedAlleles.selectedPage`,
            categoryChanged: signal`modals.addExcludedAlleles.categoryChanged`,
            geneChanged: signal`modals.addExcludedAlleles.geneChanged`,
            pageChanged: signal`modals.addExcludedAlleles.pageChanged`,
            includeAlleleClicked: signal`modals.addExcludedAlleles.includeAlleleClicked`,
            excludeAlleleClicked: signal`modals.addExcludedAlleles.excludeAlleleClicked`,
            closeAddExcludedClicked: signal`modals.addExcludedAlleles.closeAddExcludedClicked`
        },
        'AddExcludedAlleles',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                $ctrl.modelCategory = 'all'

                Object.assign($ctrl, {
                    close() {
                        $ctrl.closeAddExcludedClicked({
                            includedAlleleIds: $ctrl.includedAlleleIds
                        })
                    }
                })
            }
        ]
    )
})
