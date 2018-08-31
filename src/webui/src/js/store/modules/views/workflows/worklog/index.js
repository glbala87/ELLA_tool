import { Module } from 'cerebral'
import messageChanged from './signals/messageChanged'
import addMessageClicked from './signals/addMessageClicked'
import clearWarningClicked from './signals/clearWarningClicked'
import priorityChanged from './signals/priorityChanged'
import updateReviewCommentClicked from './signals/updateReviewCommentClicked'

export default Module({
    state: {
        message: null
    },
    signals: {
        messageChanged,
        addMessageClicked,
        clearWarningClicked,
        priorityChanged,
        updateReviewCommentClicked
    }
})
