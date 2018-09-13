var Page = require('./page')
let util = require('./util')

const SELECTOR_NEW_MESSAGE = '.interpretation-log .compose .control-comment'
const SELECTOR_NEW_MESSAGE_EDITOR = `${SELECTOR_NEW_MESSAGE} .wysiwygeditor`
const SELECTOR_NEW_MESSAGE_BUTTON = '.interpretation-log .compose .id-add-message-btn'
const SELECTOR_LAST_MESSAGE_EDITOR = '.interpretation-log .messages>div:last-child .wysiwygeditor'

class WorkLog extends Page {
    open() {
        let buttonSelector = 'button.id-worklog'
        browser.click(buttonSelector)
        browser.waitForExist('.interpretationlog-popover', 100) // make sure the popover appeared
        browser.pause(500) // Wait for popover animation to settle
    }

    close() {
        browser.click('body')
        browser.pause(500) // Wait for popover animation to settle
    }

    get newMessageElement() {
        return util.elementIntoView(SELECTOR_NEW_MESSAGE)
    }

    get newMessageButtonElement() {
        return util.elementIntoView(SELECTOR_NEW_MESSAGE_BUTTON)
    }

    get reviewCommentElement() {
        return browser.element('.interpretation-log input.id-review-comment')
    }

    get reviewCommentUpdateBtn() {
        return browser.element('.interpretation-log button.id-review-comment-update')
    }

    addMessage(text) {
        this.newMessageElement.click()
        browser.setValue(SELECTOR_NEW_MESSAGE_EDITOR, text)
        this.newMessageButtonElement.click()
    }

    getLastMessage() {
        return browser.getText(SELECTOR_LAST_MESSAGE_EDITOR)
    }
}

module.exports = WorkLog
