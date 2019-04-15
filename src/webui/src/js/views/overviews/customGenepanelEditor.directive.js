import app from '../../ng-decorators'
import { Compute } from 'cerebral'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './customGenepanelEditor.ngtmpl.html'

const candidatesFilteredTotalItems = Compute(
    state`views.overview.import.candidates.filteredFlattened`,
    (flattened) => {
        if (!flattened) {
            return 0
        }
        return flattened.length
    }
)

const candidatesTotalItems = Compute(state`views.overview.import.data.genepanel`, (genepanel) => {
    if (!genepanel) {
        return 0
    }
    let length = 0
    for (const gene of Object.values(genepanel.genes)) {
        length += gene.transcripts.length
    }
    return length
})

const candidateTranscripts = Compute(
    state`views.overview.import.candidates.filteredFlattened`,
    state`views.overview.import.added.addedGenepanel`,
    state`views.overview.import.candidates.selectedPage`,
    state`views.overview.import.candidates.perPage`,
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
    state`views.overview.import.added.filteredFlattened`,
    state`views.overview.import.added.selectedPage`,
    state`views.overview.import.added.perPage`,
    (added, selectedPage, perPage) => {
        if (!added) {
            return []
        }
        return added.slice((selectedPage - 1) * perPage, selectedPage * perPage)
    }
)

const addedFilteredTotalItems = Compute(
    state`views.overview.import.added.filteredFlattened`,
    (added) => {
        if (!added) {
            return 0
        }
        return added.length
    }
)

const addedTotalItems = Compute(state`views.overview.import.added.addedGenepanel`, (genepanel) => {
    if (!genepanel) {
        return 0
    }
    let length = 0
    for (const gene of Object.values(genepanel.genes)) {
        length += gene.transcripts.length
    }
    return length
})

app.component('customGenepanelEditor', {
    templateUrl: 'customGenepanelEditor.ngtmpl.html',
    controller: connect(
        {
            candidateTranscripts,
            addedTranscripts,
            genepanels: state`views.overview.import.data.genepanels`,
            selectedGenepanel: state`views.overview.import.selectedGenepanel`,
            addedGenepanel: state`views.overview.import.added.addedGenepanel`,
            candidatesTotalItems,
            candidatesFilteredTotalItems,
            addedTotalItems,
            addedFilteredTotalItems,
            candidatesSelectedPage: state`views.overview.import.candidates.selectedPage`,
            candidatesPerPage: state`views.overview.import.candidates.perPage`,
            candidatesFilter: state`views.overview.import.candidates.filter`,
            addedPerPage: state`views.overview.import.added.perPage`,
            addedFilter: state`views.overview.import.added.filter`,
            addTranscriptClicked: signal`views.overview.import.addTranscriptClicked`,
            removeTranscriptClicked: signal`views.overview.import.removeTranscriptClicked`,
            addAllTranscriptsClicked: signal`views.overview.import.addAllTranscriptsClicked`,
            removeAllTranscriptsClicked: signal`views.overview.import.removeAllTranscriptsClicked`,
            candidatesFilterChanged: signal`views.overview.import.candidatesFilterChanged`,
            addedFilterChanged: signal`views.overview.import.addedFilterChanged`,
            customGenepanelNameChanged: signal`views.overview.import.customGenepanelNameChanged`,
            selectedCandidatesPageChanged: signal`views.overview.import.selectedCandidatesPageChanged`,
            selectedAddedPageChanged: signal`views.overview.import.selectedAddedPageChanged`,
            selectedGenepanelChanged: signal`views.overview.import.selectedGenepanelChanged`
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
                        if ($ctrl.candidatesFilter && $ctrl.candidatesFilter.length) {
                            return `${$ctrl.candidatesFilteredTotalItems} transcripts`
                        } else {
                            return `${$ctrl.candidatesTotalItems} available transcripts`
                        }
                    },
                    getCandidatesFilterSubText() {
                        if ($ctrl.candidatesFilter && $ctrl.candidatesFilter.length) {
                            return `(of ${$ctrl.candidatesTotalItems}) from current filter`
                        } else {
                            ;('')
                        }
                    },
                    getAddedFilterText() {
                        if ($ctrl.addedFilter && $ctrl.addedFilter.length) {
                            return `${$ctrl.addedFilteredTotalItems} transcripts`
                        } else {
                            return `${$ctrl.addedTotalItems} added transcripts`
                        }
                    },
                    getAddedFilterSubText() {
                        if ($ctrl.addedFilter && $ctrl.addedFilter.length) {
                            return `(of ${$ctrl.addedTotalItems}) from current filter`
                        } else {
                            ;('')
                        }
                    }
                })
            }
        ]
    )
})
