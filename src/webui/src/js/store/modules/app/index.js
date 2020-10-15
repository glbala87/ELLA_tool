import { Module } from 'cerebral'
import updateBroadcastTriggered from './signals/updateBroadcastTriggered'
import logException from './signals/logException'

export default Module({
    state: {
        config: null,
        broadcast: {
            messages: null
        },
        user: null
    },
    signals: {
        updateBroadcastTriggered,
        logException
    }
})
