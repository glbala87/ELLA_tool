import { sequence, parallel } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import progress from '../../../../common/factories/progress'
import loadAlleles from '../sequences/loadAlleles'
import loadReferences from '../sequences/loadReferences'
import loadAttachments from '../sequences/loadAttachments'
import loadAcmg from '../sequences/loadAcmg'

import toastr from '../../../../common/factories/toastr'

export default sequence('LoadInterpretationData', [
    progress('start'),
    loadAlleles,
    progress('inc'),
    parallel([[loadReferences, loadAcmg], loadAttachments]),
    progress('done')
])
