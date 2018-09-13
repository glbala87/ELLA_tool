import { Module } from 'cerebral'
import messageChanged from './signals/messageChanged'
import addMessageClicked from './signals/addMessageClicked'
import editMessageClicked from './signals/editMessageClicked'
import deleteMessageClicked from './signals/deleteMessageClicked'
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
        editMessageClicked,
        deleteMessageClicked,
        clearWarningClicked,
        priorityChanged,
        updateReviewCommentClicked
    }
})
