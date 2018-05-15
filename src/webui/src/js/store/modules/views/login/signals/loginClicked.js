import { set, equals, unset } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'
import toastr from '../../../../common/factories/toastr'
import checkUsername from '../actions/checkUsername'
import postLogin from '../actions/postLogin'
import reset from '../actions/reset'

export default [
    checkUsername,
    {
        pass: [
            postLogin,
            {
                // Unset config here; this is reloaded (with user config) on redirect
                success: [reset, unset(state`app.config`), redirect('overview/variants')],
                error: [
                    set(state`views.login.password`, ''),
                    toastr('error', string`${props`errorMessage`}`)
                ]
            }
        ],
        fail: [toastr('error', 'Invalid username')]
    }
]
