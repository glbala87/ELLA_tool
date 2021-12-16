import { Module } from 'cerebral'
import dismissClicked from './signals/dismissClicked'
import showEvaluateReferenceClicked from './signals/showEvaluateReferenceClicked'
import evaluationChanged from './signals/evaluationChanged'
import sourcesChanged from './signals/sourcesChanged'

export default Module({
    state: {
        show: false
    },
    signals: {
        dismissClicked,
        showEvaluateReferenceClicked,
        evaluationChanged,
        sourcesChanged
    }
})
