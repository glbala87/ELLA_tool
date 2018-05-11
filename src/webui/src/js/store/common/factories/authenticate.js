import { sequence } from 'cerebral'
import { set, when } from 'cerebral/operators'
import { redirect } from '@cerebral/router/operators'
import { state, props } from 'cerebral/tags'
import { getUser } from '../actions'

function authenticate(continueSequence) {
    return sequence('authenticate', [
        when(state`app.user`),
        {
            true: continueSequence,
            false: [
                getUser,
                {
                    success: [
                        // FIXME: Temporary until we've migrated to cerebral.
                        // Copy user into Angular service
                        ({ User, props }) => {
                            User.setCurrentUser(props.result)
                        },
                        set(state`app.user`, props`result`),
                        continueSequence
                    ],
                    error: redirect('/login')
                }
            ]
        }
    ])
}

export default authenticate
