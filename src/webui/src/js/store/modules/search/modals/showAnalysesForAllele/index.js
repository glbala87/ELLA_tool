import { Module } from 'cerebral'
import showAnalysesForAlleleClicked from './signals/showAnalysesForAlleleClicked'
import warningAcceptedClicked from './signals/warningAcceptedClicked'
import copyAnalysesForAlleleClicked from './signals/copyAnalysesForAlleleClicked'
import dismissClicked from './signals/dismissClicked'

export default Module({
    modules: {},
    state: {},
    signals: {
        showAnalysesForAlleleClicked,
        warningAcceptedClicked,
        copyAnalysesForAlleleClicked,
        dismissClicked
    }
})
