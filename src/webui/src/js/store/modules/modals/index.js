import { Module } from 'cerebral'
import showAnalysesForAlleleAccepted from './signals/showAnalysesForAlleleAccepted'
import copyAnalysesForAlleleClicked from './signals/copyAnalysesForAlleleClicked'

export default Module({
    state: {},
    signals: {
        showAnalysesForAlleleAccepted,
        copyAnalysesForAlleleClicked
    }
})
