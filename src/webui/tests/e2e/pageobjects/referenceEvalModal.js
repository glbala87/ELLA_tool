let Page = require('./page')

const TOP_CLASS = '.id-reference-modal-body'

class ReferenceEvalModal extends Page {
    get comment() {
        return $(`${TOP_CLASS} .id-reference-comment`)
    }
    get saveBtn() {
        return $(`${TOP_CLASS} button.id-reference-modal-save`)
    }

    setRelevance(index) {
        $(`${TOP_CLASS} article.id-relevance label:nth-child(${index})`).click()
    }

    setComment(text) {
        this.comment.click()
        let selector = `${TOP_CLASS} .id-reference-comment .wysiwygeditor`
        $(selector).setValue(text)
    }

    waitForClose() {
        $(TOP_CLASS).waitForExist(10000, true)
    }
}

module.exports = ReferenceEvalModal
