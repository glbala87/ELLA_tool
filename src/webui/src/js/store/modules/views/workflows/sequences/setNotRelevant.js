import setNotRelevant from '../actions/setNotRelevant';
import allelesChanged from '../alleleSidebar/sequences/allelesChanged';
import checkAddRemoveAlleleToReport from '../interpretation/actions/checkAddRemoveAllelesToReport';
import setDirty from '../interpretation/actions/setDirty';

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
