import { unset } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import isReadOnly from '../operators/isReadOnly'
import postGeneAssessment from '../actions/postGeneAssessment'
import loadGenepanel from '../../sequences/loadGenepanel'
import toast from '../../../../../common/factories/toast'

export default [
    isReadOnly,
    {
        true: [],
        false: [
            postGeneAssessment,
            {
                success: [
                    loadGenepanel,
                    unset(
                        state`views.workflows.interpretation.userState.geneassessment.${props`geneAssessment.gene_id`}`
                    )
                ],
                error: [toast('error', 'Failed to update gene information.')]
            }
        ]
    }
]
