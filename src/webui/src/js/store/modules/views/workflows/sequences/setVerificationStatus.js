import setVerificationStatus from '../actions/setVerificationStatus'
import allelesChanged from '../alleleSidebar/sequences/allelesChanged'
import checkAddRemoveAlleleToReport from '../interpretation/actions/checkAddRemoveAllelesToReport'
import setDirty from '../interpretation/actions/setDirty'

export default [
    setDirty,
    setVerificationStatus,
    ({ props }) => {
        return {
            checkReportAlleleIds: [props.alleleId]
        }
    },
    checkAddRemoveAlleleToReport,
    allelesChanged
]
