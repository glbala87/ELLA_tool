var Page = require('./page')

class AddExcludedModal extends Page {

    get includeAlleleBtn() { return browser.element('.id-add-excluded-modal .id-include-allele'); }
    get excludeAlleleBtn() { return browser.element('.id-add-excluded-modal .id-exclude-allele'); }
    get closeBtn() { return browser.element('.id-add-excluded-modal .id-close'); }

}

module.exports = AddExcludedModal;