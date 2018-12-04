import { set, when } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'
import toast from '../../../../common/factories/toast'
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
                            toast(
                                'success',
                                `Password changed successfully. You can now login with your new password.`,
                                10000
                            ),
                            set(state`views.login.mode`, 'Login'),
                            set(state`views.login.password`, ''),
                            set(state`views.login.newPassword`, ''),
                            set(state`views.login.confirmNewPassword`, '')
                        ],
                        error: [toast('error', string`${props`errorMessage`}`)]
                    }
                ],
                false: [toast('error', `Password is invalid or confirm doesn't match.`)]
            }
        ],
        fail: [toast('error', 'Invalid username')]
    }
]
