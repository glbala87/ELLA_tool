var Page = require('./page')
let util = require('./util')

const SELECTOR_NEW_MESSAGE = '.interpretation-log .compose .control-comment'
const SELECTOR_NEW_MESSAGE_EDITOR = `${SELECTOR_NEW_MESSAGE} .wysiwygeditor`
const SELECTOR_NEW_MESSAGE_BUTTON = '.interpretation-log .compose .id-add-message-btn'
const SELECTOR_LAST_MESSAGE_EDITOR = '.interpretation-log .messages>div:last-child .wysiwygeditor'

class WorkLog extends Page {
    open() {
        $('button.id-worklog').click()
        $('.interpretationlog-popover').waitForExist()
        browser.pause(500) // Wait for popover animation to settle
    }

    close() {
        $('body').click()
        browser.pause(500) // Wait for popover animation to settle
    }

    get newMessageElement() {
        return util.elementIntoView(SELECTOR_NEW_MESSAGE)
    }

    get newMessageButtonElement() {
        return util.elementIntoView(SELECTOR_NEW_MESSAGE_BUTTON)
    }

    get reviewCommentElement() {
        return $('.interpretation-log input.id-review-comment')
    }

    get reviewCommentUpdateBtn() {
        return $('.interpretation-log button.id-review-comment-update')
    }

    addMessage(text) {
        this.newMessageElement.click()
        $(SELECTOR_NEW_MESSAGE_EDITOR).setValue(text)
        this.newMessageButtonElement.click()
    }

    getLastMessage() {
        return $(SELECTOR_LAST_MESSAGE_EDITOR).getText()
    }
}

module.exports = WorkLog
