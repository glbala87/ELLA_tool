var Page = require('./page')

class CustomAnnotationModal extends Page {

    get annotationSelect() { return browser.element('.id-custom-annotation-modal .id-annotation-select'); }
    get valueSelect() { return browser.element('.id-custom-annotation-modal .id-value-select'); }
    get addBtn() { return browser.element('.id-custom-annotation-modal .id-add-annotation'); }
    get saveBtn() { return browser.element('.id-custom-annotation-modal .id-save'); }
    get cancelBtn() { return browser.element('.id-custom-annotation-modal .id-cancel'); }

}

module.exports = CustomAnnotationModal