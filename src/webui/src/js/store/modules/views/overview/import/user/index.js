import { Module } from 'cerebral'
import jobDataChanged from './signals/jobDataChanged'
import selectionChanged from './signals/selectionChanged'
import toggleCollapsed from './signals/toggleCollapsed'
import updateAnalysisOptions from './signals/updateAnalysisOptions'

export default Module({
    state: {}, // State set in changeView
    signals: {
        jobDataChanged,
        toggleCollapsed,
        selectionChanged,
        updateAnalysisOptions
    }
})
