import { Module } from 'cerebral'
import dismissClicked from './signals/dismissClicked'
import selectedModeChanged from './signals/selectedModeChanged'
import selectedChanged from './signals/selectedChanged'
import showAlleleAssessmentHistoryClicked from './signals/showAlleleAssessmentHistoryClicked'

export default Module({
    state: {
        show: false
    },
    signals: {
        dismissClicked,
        selectedModeChanged,
        showAlleleAssessmentHistoryClicked,
        selectedChanged
    }
})
