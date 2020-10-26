import { Module } from 'cerebral'
import dismissClicked from './signals/dismissClicked'
import selectedAlleleAssessmentChanged from './signals/selectedAlleleAssessmentChanged'
import showAlleleAssessmentHistoryClicked from './signals/showAlleleAssessmentHistoryClicked'

export default Module({
    state: {
        show: false
    },
    signals: {
        dismissClicked,
        selectedAlleleAssessmentChanged,
        showAlleleAssessmentHistoryClicked
    }
})
