import { Module } from 'cerebral'
import dismissClicked from './signals/dismissClicked'
import selectedModeChanged from './signals/selectedModeChanged'
import selectedChanged from './signals/selectedChanged'
import showAlleleHistoryClicked from './signals/showAlleleHistoryClicked'

export default Module({
    state: {
        show: false
    },
    signals: {
        dismissClicked,
        selectedModeChanged,
        showAlleleHistoryClicked,
        selectedChanged
    }
})
