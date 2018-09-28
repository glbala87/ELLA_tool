import { Module } from 'cerebral'
import updateBroadcastTriggered from './signals/updateBroadcastTriggered'

export default Module({
    state: {
        config: null,
        broadcast: {
            messages: null
        },
        user: null
    },
    signals: {
        updateBroadcastTriggered
    }
})
