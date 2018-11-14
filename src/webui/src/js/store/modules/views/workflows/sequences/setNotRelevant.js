import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import setNotRelevant from '../actions/setNotRelevant'
import setDirty from '../interpretation/actions/setDirty'
import checkAddRemoveAlleleToReport from '../interpretation/actions/checkAddRemoveAllelesToReport'
import allelesChanged from '../alleleSidebar/sequences/allelesChanged'

export default [
    setDirty,
    setNotRelevant,
    ({ props }) => {
        return {
            checkReportAlleleIds: [props.alleleId]
        }
    },
    checkAddRemoveAlleleToReport,
    allelesChanged
]
