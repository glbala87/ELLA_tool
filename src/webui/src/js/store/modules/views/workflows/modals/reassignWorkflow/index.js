import { Module } from 'cerebral'
import reassignWorkflowClicked from './signals/reassignWorkflowClicked'
import dismissClicked from './signals/dismissClicked'

export default Module({
    state: {
        show: false
    },
    signals: {
        reassignWorkflowClicked,
        dismissClicked
    }
})
