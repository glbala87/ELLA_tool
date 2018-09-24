import { sequence, parallel } from 'cerebral'
import progress from '../../../../common/factories/progress'
import loadGenepanel from '../sequences/loadGenepanel'
import loadAlleles from '../sequences/loadAlleles'
import loadReferences from '../sequences/loadReferences'
import loadAttachments from '../sequences/loadAttachments'
import loadAcmg from '../sequences/loadAcmg'

export default sequence('loadInterpretationData', [
    progress('start'),
    loadGenepanel,
    loadAlleles,
    progress('inc'),
    parallel([[loadReferences, loadAcmg], loadAttachments]),
    progress('done')
])
