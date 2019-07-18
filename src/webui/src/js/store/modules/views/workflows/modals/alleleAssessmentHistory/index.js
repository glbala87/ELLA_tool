import { Module } from 'cerebral'
import dismissClicked from './signals/dismissClicked'
import selectedAlleleAssessmentChanged from './signals/selectedAlleleAssessmentChanged'
import selectedViewModeChanged from './signals/selectedViewModeChanged'
import showAlleleAssessmentHistoryClicked from './signals/showAlleleAssessmentHistoryClicked'

export default Module({
    state: {
        show: false,
        selectedViewMode: 'normal',
        selectedAlleleAssessment: null
    },
    signals: {
        dismissClicked,
        selectedViewModeChanged,
        selectedAlleleAssessmentChanged,
        showAlleleAssessmentHistoryClicked
    }
})
