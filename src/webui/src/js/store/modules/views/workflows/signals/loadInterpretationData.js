import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import { sequence, parallel } from 'cerebral'
import progress from '../../../../common/factories/progress'
import loadGenepanel from '../sequences/loadGenepanel'
import loadAlleles from '../sequences/loadAlleles'
import loadReferences from '../sequences/loadReferences'
import loadAttachments from '../sequences/loadAttachments'
import loadAcmg from '../sequences/loadAcmg'
import getSelectedFilterResults from '../actions/getSelectedFilterResults'
import toast from '../../../../common/factories/toast'
import updateLoadingPhase from '../factories/updateLoadingPhase'

export default sequence('loadInterpretationData', [
    progress('start'),
    updateLoadingPhase('filtering'),
    getSelectedFilterResults,
    {
        error: [toast('error', 'Failed to fetch filtered alleles', 30000)],
        success: [
            set(
                state`views.workflows.interpretation.filteredAlleleIds.allele_ids`,
                props`allele_ids`
            ),
            set(
                state`views.workflows.interpretation.filteredAlleleIds.excluded_allele_ids`,
                props`excluded_allele_ids`
            ),
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
