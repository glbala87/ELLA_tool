import { sequence, parallel } from 'cerebral'
import { set, when } from 'cerebral/operators'
import progress from '../../../../common/factories/progress'
import loadGenepanel from '../sequences/loadGenepanel'
import loadAlleles from '../sequences/loadAlleles'
import loadReferences from '../sequences/loadReferences'
import loadAttachments from '../sequences/loadAttachments'
import loadAcmg from '../sequences/loadAcmg'
import getSelectedInterpretation from '../computed/getSelectedInterpretation'

export default sequence('loadInterpretationData', [
    progress('start'),
    // TODO: Should be moved to getFilteredAlleles when endpoint is available
    [
        ({ state, resolve }) => {
            if (state.get('views.workflows.type') === 'analysis') {
                const selectedInterpretation = resolve.value(getSelectedInterpretation)
                state.set(
                    'views.workflows.interpretation.data.filteredAlleleIds.allele_ids',
                    selectedInterpretation.allele_ids
                )
                state.set(
                    'views.workflows.interpretation.data.filteredAlleleIds.excluded_allele_ids',
                    selectedInterpretation.excluded_allele_ids
                )
            } else {
                state.set('views.workflows.interpretation.data.filteredAlleleIds.allele_ids', [
                    state.get(`views.workflows.id`)
                ])
                state.set(
                    'views.workflows.interpretation.data.filteredAlleleIds.excluded_allele_ids',
                    {}
                )
            }
        }
    ],
    loadGenepanel,
    loadAlleles,
    progress('inc'),
    parallel([[loadReferences, loadAcmg], loadAttachments]),
    progress('done')
])
