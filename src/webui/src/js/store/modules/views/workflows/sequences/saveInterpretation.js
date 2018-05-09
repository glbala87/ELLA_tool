import patchInterpretation from '../actions/patchInterpretation'
import { set } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import toastr from '../../../../common/factories/toastr'

export default function(continueSequence) {
    return [
        patchInterpretation,
        {
            success: [set(state`views.workflows.interpretation.dirty`, false), continueSequence],
            error: [
                ({ props }) => {
                    return {
                        errorMessage:
                            props.response.status === 409
                                ? props.response.result
                                : 'Cannot save: something went wrong while saving your work. To avoid losing it, please keep this window open and contact support'
                    }
                },
                toastr('error', string`${props`errorMessage`}`)
            ]
        }
    ]
}
