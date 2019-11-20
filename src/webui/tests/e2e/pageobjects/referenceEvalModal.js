let Page = require('./page')

const TOP_CLASS = '.id-reference-modal-body'
const SELECTOR_COMMENT = `${TOP_CLASS} .id-reference-comment`
const SELECTOR_COMMENT_EDITOR = `${TOP_CLASS} .id-reference-comment .wysiwygeditor`

class ReferenceEvalModal extends Page {
    get comment() {
        return $(`${TOP_CLASS} .id-reference-comment`)
    }
    get saveBtn() {
        return $(`${TOP_CLASS} button.id-reference-modal-save`)
    }

    setRelevance(index) {
        const selector = `${TOP_CLASS} article.id-relevance label:nth-child(${index})`
        const el = $(selector)
        el.waitForDisplayed()
        el.click()
    }

    setComment(text, second) {
        $(SELECTOR_COMMENT).waitForDisplayed()
        browser.setWysiwygValue(SELECTOR_COMMENT, SELECTOR_COMMENT_EDITOR, text)
    }

    waitForClose() {
        $(TOP_CLASS).waitForExist(undefined, true)
    }
}

module.exports = ReferenceEvalModal
