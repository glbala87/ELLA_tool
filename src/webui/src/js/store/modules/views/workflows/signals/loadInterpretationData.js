import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import { sequence, parallel } from 'cerebral'
import progress from '../../../../common/factories/progress'
import loadGenepanel from '../sequences/loadGenepanel'
import loadAlleles from '../sequences/loadAlleles'
import loadReferences from '../sequences/loadReferences'
import loadAttachments from '../sequences/loadAttachments'
import loadAcmg from '../sequences/loadAcmg'
import getFilteredAlleles from '../actions/getFilteredAlleles'
import toast from '../../../../common/factories/toast'
import updateLoadingPhase from '../factories/updateLoadingPhase'
import getFilterConfig from '../../../modals/addExcludedAlleles/actions/getFilterConfig'
import setDefaultFilterConfig from '../actions/setDefaultFilterConfig'

export default sequence('loadInterpretationData', [
    progress('start'),
    when(state`views.workflows.type`, (type) => type === 'analysis'),
    {
        true: [setDefaultFilterConfig],
        false: []
    },
    getFilterConfig,
    {
        success: [set(state`views.workflows.interpretation.data.filterConfig`, props`result`)],
        error: [toast('error', 'Failed to fetch filter config', 30000)]
    },
    updateLoadingPhase('filtering'),
    getFilteredAlleles,
    {
        error: [toast('error', 'Failed to fetch filtered alleles', 30000)],
        success: [
            set(state`views.workflows.interpretation.data.filteredAlleleIds`, props`result`),
            updateLoadingPhase('variants'),
            loadGenepanel,
            loadAlleles,
            progress('inc'),
            parallel([[loadReferences, loadAcmg], loadAttachments]),
            updateLoadingPhase('done'),
            progress('done')
        ]
    }
])
