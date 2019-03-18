import { Module } from 'cerebral'
import showFinishConfirmationClicked from './signals/showFinishConfirmationClicked'
import finishConfirmationClicked from './signals/finishConfirmationClicked'
import dismissClicked from './signals/dismissClicked'

export default Module({
    state: {
        show: false
    },
    signals: {
        showFinishConfirmationClicked,
        finishConfirmationClicked,
        dismissClicked
    }
})
