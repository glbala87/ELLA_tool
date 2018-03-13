import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import setVerificationStatus from '../actions/setVerificationStatus'
import setDirty from '../interpretation/actions/setDirty'
import checkAddRemoveAlleleToReport from '../interpretation/actions/checkAddRemoveAllelesToReport'
import allelesChanged from '../alleleSidebar/sequences/allelesChanged'

export default [
    setDirty,
    setVerificationStatus,
    ({ props }) => {
        return {
            changedAlleleIds: [props.alleleId]
        }
    },
    checkAddRemoveAlleleToReport,
    allelesChanged
]
