import { set, when, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'
import saveInterpretation from '../sequences/saveInterpretation'
import finishWorkflow from '../factories/finishWorkflow'
import canFinalize from '../computed/canFinalize'
import toastr from '../../../../common/factories/toastr'
import closeModal from '../../../../common/actions/closeModal'
import setNavbarTitle from '../../../../common/factories/setNavbarTitle'

export default [
    equals(props`finishAction`),
    {
        markreview: saveInterpretation([
            finishWorkflow('markreview'),
            {
                success: [redirect('/overview')],
                error: [toastr('error', 'Something went wrong while marking workflow for review')]
            }
        ]),
        finalize: [
            ({ resolve, path }) => {
                return resolve.value(canFinalize) ? path.true() : path.false()
            },
            {
                true: saveInterpretation([
                    finishWorkflow('finalize'),
                    {
                        success: [redirect('/overview')],
                        error: [toastr('error', 'Something went wrong while finalizing workflow')]
                    }
                ]),
                false: [toastr('error', 'Tried to finalize workflow when requirements not met.')]
            }
        ]
    },
    set(props`modalName`, 'finishConfirmation'),
    closeModal
]
