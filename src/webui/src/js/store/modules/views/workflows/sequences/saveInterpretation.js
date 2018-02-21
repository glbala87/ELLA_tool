import patchInterpretation from '../actions/patchInterpretation'
import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toastr from '../../../../common/factories/toastr'

export default function(continueSequence) {
    return [
        patchInterpretation,
        {
            success: [set(state`views.workflows.interpretation.dirty`, false), continueSequence],
            error: [
                toastr(
                    'error',
                    `Cannot finish: something went wrong while saving your work. To avoid losing it, please keep this window open and contact support.`
                )
            ]
        }
    ]
}
