import { unset } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import postGeneAssessment from '../actions/postGeneAssessment'
import loadGenepanel from '../../sequences/loadGenepanel'
import toast from '../../../../../common/factories/toast'

export default [
    postGeneAssessment,
    {
        success: [
            loadGenepanel,
            unset(
                state`views.workflows.interpretation.geneInformation.geneassessment.${props`geneAssessment.gene_id`}`
            )
        ],
        error: [toast('error', 'Failed to update gene information.')]
    }
]
