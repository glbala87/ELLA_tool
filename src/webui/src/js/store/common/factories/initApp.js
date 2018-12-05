import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import { getConfig } from '../actions'
import toast from './toast'
import loadBroadcast from '../sequences/loadBroadcast'
import interval from './interval'

const BROADCAST_UPDATE_INTERVAL = 10 * 60 * 1000

function initApp(continueSequence) {
    return [
        when(state`app.config`),
        {
            true: continueSequence,
            false: [
                getConfig,
                {
                    success: [
                        // FIXME: Temporary until we've migrated to cerebral.
                        // Copy config into Angular service
                        ({ Config, props }) => {
                            Config.setConfig(props.result)
                        },
                        set(state`app.config`, props`result`),
                        continueSequence
                    ],
                    error: [
                        set(state`app.config`, null),
                        toast(
                            'error',
                            'ella cannot start. Please contact support: "Failed to load configuration"',
                            10000000
                        )
                    ]
                }
            ]
        },
        when(state`app.broadcast.messages`),
        {
            true: [],
            false: [
                // Load broadcast and set to be called at intervals
                interval(
                    'start',
                    'app.updateBroadcastTriggered',
                    {},
                    BROADCAST_UPDATE_INTERVAL,
                    true
                )
            ]
        }
    ]
}

export default initApp
