var Page = require('./page')

class CustomAnnotationModal extends Page {

    get annotationSelect() { return browser.element('.id-custom-annotation-modal .id-annotation-select'); }
    get valueSelect() { return browser.element('.id-custom-annotation-modal .id-value-select'); }
    get addBtn() { return browser.element('.id-custom-annotation-modal .id-add-annotation'); }
    get saveBtn() { return browser.element('.id-custom-annotation-modal .id-save'); }
    get cancelBtn() { return browser.element('.id-custom-annotation-modal .id-cancel'); }
    get pubMedBtn() {return browser.element('.id-referenceMode-PubMed')}
    get addReferenceBtn() { return browser.element('.id-custom-annotation-modal .id-add-reference-button');}
    get xmlInput() { return browser.element('.id-custom-annotation-modal .id-reference-xml');}
    get xmlInputEditor() { return browser.element('.id-custom-annotation-modal .id-reference-xml textarea');}

    setText(element, text) {
           browser.selectorExecute(element.selector,
            function(matchingElements, msg) {
               let e = matchingElements[0];
               e.value = msg;
               // make Angular aware of the change:
               e.dispatchEvent(new Event("input", { bubbles: true })); //Works
           }, text);
    }

    referenceList() {
        let selector = '.id-custom-annotation-modal .id-references-list article';
        if (browser.isExisting(selector)) {
            let elements = browser.elements(selector);
            return elements;
        }
    }

}

module.exports = CustomAnnotationModal;