import app from '../../ng-decorators'
import { Compute } from 'cerebral'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './customGenepanelEditor.ngtmpl.html'

const candidatesFilteredTotalItems = Compute(
    state`views.overview.import.custom.candidates.filteredFlattened`,
    (flattened) => {
        const result = {
            transcripts: 0,
            genes: 0
        }
        if (!flattened) {
            return result
        }

        const genes = new Set()
        for (const t of flattened) {
            result.transcripts += 1
            genes.add(t.hgnc_id)
        }
        result.genes = genes.size
        return result
    }
)

const candidateTranscripts = Compute(
    state`views.overview.import.custom.candidates.filteredFlattened`,
    state`views.overview.import.custom.added.addedGenepanel`,
    state`views.overview.import.custom.candidates.selectedPage`,
    state`views.overview.import.custom.candidates.perPage`,
    (candidatesFlattened, addedGenepanel, selectedPage, perPage) => {
        if (!candidatesFlattened) {
            return []
        }

        let paginated = candidatesFlattened.slice(
            (selectedPage - 1) * perPage,
            selectedPage * perPage
        )
        paginated = paginated.map((t) => {
            const isAdded =
                addedGenepanel &&
                t.hgnc_id in addedGenepanel.genes &&
                addedGenepanel.genes[t.hgnc_id].transcripts.find(
                    (a) => a.transcript_name === t.transcript_name
                )
            return Object.assign({ added: isAdded }, t)
        })
        return paginated
    }
)

const addedTranscripts = Compute(
    state`views.overview.import.custom.added.filteredFlattened`,
    state`views.overview.import.custom.added.selectedPage`,
    state`views.overview.import.custom.added.perPage`,
    (added, selectedPage, perPage) => {
        if (!added) {
            return []
        }
        return added.slice((selectedPage - 1) * perPage, selectedPage * perPage)
    }
)

const addedFilteredTotalItems = Compute(
    state`views.overview.import.custom.added.filteredFlattened`,
    (added) => {
        const result = {
            transcripts: 0,
            genes: 0
        }
        if (!added) {
            return result
        }

        const genes = new Set()
        for (const t of added) {
            result.transcripts += 1
            genes.add(t.hgnc_id)
        }
        result.genes = genes.size
        return result
    }
)

app.component('customGenepanelEditor', {
    templateUrl: 'customGenepanelEditor.ngtmpl.html',
    controller: connect(
        {
            candidateTranscripts,
            addedTranscripts,
            genepanels: state`views.overview.import.data.genepanels`,
            selectedGenepanel: state`views.overview.import.selectedGenepanel`,
            selectedFilterMode: state`views.overview.import.custom.selectedFilterMode`,
            addedGenepanel: state`views.overview.import.custom.added.addedGenepanel`,
            candidatesFilteredTotalItems,
            addedFilteredTotalItems,
            candidatesSelectedPage: state`views.overview.import.custom.candidates.selectedPage`,
            candidatesPerPage: state`views.overview.import.custom.candidates.perPage`,
            candidatesFilter: state`views.overview.import.custom.candidates.filter`,
            candidatesFilterBatchProcessed: state`views.overview.import.custom.candidates.filterBatchProcessed`,
            candidatesFilterBatch: state`views.overview.import.custom.candidates.filterBatch`,
            candidatesMissingBatch: state`views.overview.import.custom.candidates.missingBatch`,
            addedPerPage: state`views.overview.import.custom.added.perPage`,
            addedFilter: state`views.overview.import.custom.added.filter`,
            addTranscriptClicked: signal`views.overview.import.addTranscriptClicked`,
            removeTranscriptClicked: signal`views.overview.import.removeTranscriptClicked`,
            addAllTranscriptsClicked: signal`views.overview.import.addAllTranscriptsClicked`,
            removeAllTranscriptsClicked: signal`views.overview.import.removeAllTranscriptsClicked`,
            applyFilterBatchClicked: signal`views.overview.import.applyFilterBatchClicked`,
            candidatesFilterChanged: signal`views.overview.import.candidatesFilterChanged`,
            candidatesFilterBatchChanged: signal`views.overview.import.candidatesFilterBatchChanged`,
            addedFilterChanged: signal`views.overview.import.addedFilterChanged`,
            applyFilterBatchClicked: signal`views.overview.import.applyFilterBatchClicked`,
            clearFilterBatchClicked: signal`views.overview.import.clearFilterBatchClicked`,
            copyFilterBatchClicked: signal`views.overview.import.copyFilterBatchClicked`,
            customGenepanelNameChanged: signal`views.overview.import.customGenepanelNameChanged`,
            selectedCandidatesPageChanged: signal`views.overview.import.selectedCandidatesPageChanged`,
            selectedAddedPageChanged: signal`views.overview.import.selectedAddedPageChanged`,
            selectedGenepanelChanged: signal`views.overview.import.selectedGenepanelChanged`,
            selectedFilterModeChanged: signal`views.overview.import.selectedFilterModeChanged`
        },
        'CustomGenepanelEditor',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    getAddBtnText(transcript) {
                        return transcript.added ? 'Added' : 'Add'
                    },
                    getCandidatesFilterText() {
                        return `${$ctrl.candidatesFilteredTotalItems.transcripts} transcripts (${$ctrl.candidatesFilteredTotalItems.genes} genes)`
                    },
                    getCandidatesFilterSubText() {
                        if (
                            ($ctrl.selectedFilterMode === 'single' &&
                                $ctrl.candidatesFilter &&
                                $ctrl.candidatesFilter.length) ||
                            ($ctrl.selectedFilterMode === 'batch' &&
                                $ctrl.candidatesFilterBatchProcessed)
                        ) {
                            return 'from filter'
                        }
                        return ''
                    },
                    getAddedFilterText() {
                        return `${$ctrl.addedFilteredTotalItems.transcripts} transcripts (${$ctrl.addedFilteredTotalItems.genes} genes)`
                    },
                    getAddedFilterSubText() {
                        if ($ctrl.addedFilter && $ctrl.addedFilter.length) {
                            return `from filter`
                        }
                        return ''
                    }
                })
            }
        ]
    )
})
