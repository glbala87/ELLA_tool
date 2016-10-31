var Page = require('./page')

class ReferenceEvalModal extends Page {

    get comment() { return browser.element('.id-reference-modal-body textarea[placeholder="COMMENTS"]'); }
    get saveBtn() { return browser.element('.id-reference-modal-body button.id-reference-modal-save'); }

    setRelevance(index) {
        browser.click(`.id-reference-modal-body article.question:nth-child(1) label:nth-child(${index})`);
    }

    setConclusion(index) {
        browser.click(`.id-reference-modal-body article.question:nth-child(2) label:nth-child(${index})`);
    }

    setQuality(index) {
        browser.click(`.id-reference-modal-body article.question:nth-child(8) label:nth-child(${index})`);
    }


}

module.exports = ReferenceEvalModal