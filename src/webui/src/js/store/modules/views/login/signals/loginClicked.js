import { set, equals } from 'cerebral/operators'
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
                success: [reset, redirect('overview/variants')],
                error: [
                    set(state`views.login.password`, ''),
                    toastr('error', 'Login unsuccessful. Please check username and password.')
                ]
            }
        ],
        fail: [toastr('error', 'Invalid username')]
    }
]
