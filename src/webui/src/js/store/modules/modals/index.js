import { Module } from 'cerebral'
import showAnalysesForAlleleAccepted from './signals/showAnalysesForAlleleAccepted'
import copyAnalysesForAlleleClicked from './signals/copyAnalysesForAlleleClicked'
import addExcludedAlleles from './addExcludedAlleles'

export default Module({
    modules: {
        addExcludedAlleles
    },
    state: {},
    signals: {
        showAnalysesForAlleleAccepted,
        copyAnalysesForAlleleClicked
    }
})
