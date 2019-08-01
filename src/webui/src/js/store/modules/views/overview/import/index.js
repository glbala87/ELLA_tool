import { Module } from 'cerebral'
import customGenepanelSelected from './signals/customGenepanelSelected'
import importSourceTypeSelected from './signals/importSourceTypeSelected'
import customGenepanelNameChanged from './signals/customGenepanelNameChanged'
import addTranscriptClicked from './signals/addTranscriptClicked'
import removeTranscriptClicked from './signals/removeTranscriptClicked'
import addAllTranscriptsClicked from './signals/addAllTranscriptsClicked'
import removeAllTranscriptsClicked from './signals/removeAllTranscriptsClicked'
import importHistoryPageChanged from './signals/importHistoryPageChanged'
import importClicked from './signals/importClicked'
import candidatesFilterChanged from './signals/candidatesFilterChanged'
import resetImportJobClicked from './signals/resetImportJobClicked'
import updateImportJobsTriggered from './signals/updateImportJobsTriggered'
import sampleSelected from './signals/sampleSelected'
import samplesSearchChanged from './signals/samplesSearchChanged'
import selectedCandidatesPageChanged from './signals/selectedCandidatesPageChanged'
import selectedAddedPageChanged from './signals/selectedAddedPageChanged'
import addedFilterChanged from './signals/addedFilterChanged'
import selectedGenepanelChanged from './signals/selectedGenepanelChanged'
import priorityChanged from './signals/priorityChanged'
import selectedFilterModeChanged from './signals/selectedFilterModeChanged'
import applyFilterBatchClicked from './signals/applyFilterBatchClicked'

export default Module({
    state: {}, // State set in changeView
    signals: {
        candidatesFilterChanged,
        addedFilterChanged,
        addTranscriptClicked,
        customGenepanelSelected,
        importSourceTypeSelected,
        removeTranscriptClicked,
        addAllTranscriptsClicked,
        removeAllTranscriptsClicked,
        importHistoryPageChanged,
        importClicked,
        customGenepanelNameChanged,
        resetImportJobClicked,
        sampleSelected,
        samplesSearchChanged,
        selectedCandidatesPageChanged,
        selectedAddedPageChanged,
        selectedGenepanelChanged,
        priorityChanged,
        selectedFilterModeChanged,
        applyFilterBatchClicked,
        updateImportJobsTriggered
    }
})
