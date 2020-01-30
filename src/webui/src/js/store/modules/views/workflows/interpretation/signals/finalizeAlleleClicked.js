import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import isReadOnly from '../operators/isReadOnly'
import postFinalizeAllele from '../actions/postFinalizeAllele'
import toast from '../../../../../common/factories/toast'
import saveInterpretation from '../../sequences/saveInterpretation'
import loadAlleles from '../../sequences/loadAlleles'
import progress from '../../../../../common/factories/progress'
import loadInterpretationLogs from '../../worklog/sequences/loadInterpretationLogs'

export default [
    isReadOnly,
    {
        false: [
            saveInterpretation([
                postFinalizeAllele,
                {
                    success: [
                        progress('start'),
                        loadAlleles,
                        set(
                            state`views.workflows.interpretation.state.allele.${props`alleleId`}.workflow.reviewed`,
                            true
                        ),
                        progress('done'),
                        // Don't let progress shown to user
                        // depend on work log, but "load in background"
                        loadInterpretationLogs
                    ],
                    error: [toast('error', 'Failed to create/update classification.')]
                }
            ])
        ],
        true: []
    }
]
