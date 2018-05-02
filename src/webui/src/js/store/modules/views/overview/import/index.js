import { Module } from 'cerebral'
import customGenepanelSelected from './signals/customGenepanelSelected'
import customGenepanelNameChanged from './signals/customGenepanelNameChanged'
import addTranscriptClicked from './signals/addTranscriptClicked'
import removeTranscriptClicked from './signals/removeTranscriptClicked'
import addAllTranscriptsClicked from './signals/addAllTranscriptsClicked'
import removeAllTranscriptsClicked from './signals/removeAllTranscriptsClicked'
import importClicked from './signals/importClicked'
import candidatesFilterChanged from './signals/candidatesFilterChanged'
import selectedCandidatesPageChanged from './signals/selectedCandidatesPageChanged'
import selectedAddedPageChanged from './signals/selectedAddedPageChanged'
import addedFilterChanged from './signals/addedFilterChanged'
import selectedGenepanelChanged from './signals/selectedGenepanelChanged'

export default Module({
    state: {}, // State set in changeView
    signals: {
        candidatesFilterChanged,
        addedFilterChanged,
        addTranscriptClicked,
        customGenepanelSelected,
        removeTranscriptClicked,
        addAllTranscriptsClicked,
        removeAllTranscriptsClicked,
        importClicked,
        customGenepanelNameChanged,
        selectedCandidatesPageChanged,
        selectedAddedPageChanged,
        selectedGenepanelChanged
    }
})
