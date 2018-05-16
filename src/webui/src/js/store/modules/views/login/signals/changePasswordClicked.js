import { set, when } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'
import toastr from '../../../../common/factories/toastr'
import checkUsername from '../actions/checkUsername'
import checkConfirmPassword from '../actions/checkConfirmPassword'
import postChangePassword from '../actions/postChangePassword'

export default [
    checkUsername,
    {
        pass: [
            checkConfirmPassword,
            when(state`views.login.passwordMatches`),
            {
                true: [
                    postChangePassword,
                    {
                        success: [
                            toastr('success', `Password changed successfully.`, 1000),
                            set(state`views.login.mode`, 'Login'),
                            set(state`views.login.password`, ''),
                            set(state`views.login.newPassword`, ''),
                            set(state`views.login.confirmNewPassword`, '')
                        ],
                        error: [toastr('error', string`${props`errorMessage`}`)]
                    }
                ],
                false: [toastr('error', `Password is invalid or confirm doesn't match.`)]
            }
        ],
        fail: [toastr('error', 'Invalid username')]
    }
]
