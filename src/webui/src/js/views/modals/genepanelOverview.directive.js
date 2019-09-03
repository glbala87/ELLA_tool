import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './genepanelOverview.ngtmpl.html'
import popoverTemplate from './genepanelOverviewGenePopover.ngtmpl.html'

const filteredGenes = Compute(
    state`views.workflows.modals.genepanelOverview.geneFilter`,
    state`views.workflows.modals.genepanelOverview.filteredGenesPage`,
    state`views.workflows.modals.genepanelOverview.filteredGenesPerPage`,
    state`views.workflows.modals.genepanelOverview.data.genepanel`,
    (filter, page, perPage, genepanel) => {
        if (!genepanel) {
            return []
        }
        let filtered = genepanel.genes
        if (filter) {
            filtered = filtered.filter((g) => g.hgnc_symbol.toLowerCase().startsWith(filter))
        }
        const totalFiltered = filtered.length
        return {
            genes: filtered.slice((page - 1) * perPage, page * perPage),
            totalCount: totalFiltered
        }
    }
)

const totalTranscriptsCount = Compute(
    state`views.workflows.modals.genepanelOverview.data.genepanel`,
    (genepanel) => {
        if (!genepanel) {
            return
        }
        return genepanel.genes.reduce((count, gene) => count + gene.transcripts.length, 0)
    }
)

app.component('genepanelOverview', {
    templateUrl: 'genepanelOverview.ngtmpl.html',
    controller: connect(
        {
            filteredGenes,
            totalTranscriptsCount,
            filteredGenesPerPage: state`views.workflows.modals.genepanelOverview.filteredGenesPerPage`,
            filteredGenesPage: state`views.workflows.modals.genepanelOverview.filteredGenesPage`,
            genepanel: state`views.workflows.modals.genepanelOverview.data.genepanel`,
            stats: state`views.workflows.modals.genepanelOverview.data.stats`,
            closeClicked: signal`views.workflows.modals.genepanelOverview.closeClicked`,
            geneFilterChanged: signal`views.workflows.modals.genepanelOverview.geneFilterChanged`,
            filteredGenesPageChanged: signal`views.workflows.modals.genepanelOverview.filteredGenesPageChanged`,
            copyGenesToClipboardClicked: signal`views.workflows.modals.genepanelOverview.copyGenesToClipboardClicked`
        },
        'GenepanelOverview',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    close: () => {
                        $ctrl.closeClicked()
                    },
                    formatInheritance(gene) {
                        return [...new Set(gene.phenotypes.map((p) => p.inheritance))].join(', ')
                    },
                    formatPhenotypes(gene) {
                        return gene.phenotypes.map((p) => `${p.description} (${p.inheritance})`)
                    }
                })
            }
        ]
    )
})
