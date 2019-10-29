import { set } from 'cerebral/operators'
import { state } from 'cerebral/tags'
import { wait } from 'cerebral/operators'
import postLogout from '../actions/postLogout'
import { redirect } from '../../../../common/factories/route'
import toast from '../../../../common/factories/toast'
import loadBroadcast from '../../../../common/sequences/loadBroadcast'

export default [
    toast('info', 'Logging out, please wait...', 1000),
    wait(1000),
    postLogout,
    {
        success: [
            set(state`app.user`, null),
            set(state`app.config`, null), // Force config reload
            redirect('/login'),
            loadBroadcast
        ],
        error: [toast('error', 'Something went wrong when logging out.', 10000)]
    }
]
