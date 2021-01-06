import { Module } from 'cerebral'
import showAddExternalClicked from './signals/showAddExternalClicked'
import dismissClicked from './signals/dismissClicked'
import selectionChanged from './signals/selectionChanged'
import saveClicked from './signals/saveClicked'

export default Module({
    state: {
        show: false
    },
    signals: {
        showAddExternalClicked,
        dismissClicked,
        selectionChanged,
        saveClicked
    }
})
