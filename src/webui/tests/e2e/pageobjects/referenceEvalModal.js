let Page = require('./page');

const TOP_CLASS = ".id-reference-modal-body";

class ReferenceEvalModal extends Page {

    get comment() { return browser.element(`${TOP_CLASS} .id-reference-comment`); }
    get saveBtn() { return browser.element(`${TOP_CLASS} button.id-reference-modal-save`); }

    setRelevance(index) {
        browser.click(`${TOP_CLASS} article.id-relevance label:nth-child(${index})`);
    }

    setComment(text) {
        let commentElement = this.comment;
        commentElement.click();
        let selector = `${TOP_CLASS} .id-reference-comment .wysiwygeditor`;
        browser.setValue(selector, text);
    }

}

module.exports = ReferenceEvalModal;