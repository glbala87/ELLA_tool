import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { props, state } from 'cerebral/tags'
import toast from '../../../../common/factories/toast'
import getGenepanel from '../actions/getGenepanel'
import clearSupercededGeneAssessments from '../interpretation/actions/clearSupercededGeneAssessments'

export default sequence('loadGenepanel', [
    getGenepanel,
    {
        error: [toast('error', 'Failed to load genepanel', 30000)],
        success: [
            set(state`views.workflows.interpretation.data.genepanel`, props`result`),
            clearSupercededGeneAssessments
        ]
    }
])
