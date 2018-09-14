var Page = require('./page')

class AddExcludedModal extends Page {
    includeAllele(num) {
        browser
            .element(
                `.id-add-excluded-modal .id-excluded section.allele-sidebar-list .nav-row:nth-child(${num +
                    1}) .tab .added`
            )
            .click()
        browser.pause(1000) // Can be a bit slow on very large samples
    }
    excludeAllele(num) {
        browser
            .element(
                `.id-add-excluded-modal .id-included section.allele-sidebar-list .nav-row:nth-child(${num +
                    1}) .tab .added`
            )
            .click()
        browser.pause(1000)
    }
    get closeBtn() {
        return browser.element('.id-add-excluded-modal .id-close')
    }
}

module.exports = AddExcludedModal
