import { Module } from 'cerebral'
import showAddPredictionClicked from './signals/showAddPredictionClicked'
import dismissClicked from './signals/dismissClicked'
import selectionChanged from './signals/selectionChanged'
import saveClicked from './signals/saveClicked'

export default Module({
    state: {
        show: false
    },
    signals: {
        showAddPredictionClicked,
        dismissClicked,
        selectionChanged,
        saveClicked
    }
})
