import { set } from 'cerebral/operators'
import { string, state, props } from 'cerebral/tags'

import showModal from '../../../common/actions/showModal'

export default [
    set(state`modals.showAnalysesForAllele.allele`, props`allele`),
    set(props`modalName`, string`showAnalysesForAllele`),
    showModal
]
