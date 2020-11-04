import { Module } from 'cerebral'
import showAddReferencesClicked from './signals/showAddReferencesClicked'
import dismissClicked from './signals/dismissClicked'
import selectionChanged from './signals/selectionChanged'
import saveClicked from './signals/saveClicked'
import addReference from './signals/addReference'
import removeReference from './signals/removeReference'

export default Module({
    state: {
        show: false
    },
    signals: {
        showAddReferencesClicked,
        dismissClicked,
        selectionChanged,
        saveClicked,
        addReference,
        removeReference
    }
})
