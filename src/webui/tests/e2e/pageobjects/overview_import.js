var Page = require('./page')
var util = require('./util')

class Import extends Page {
    open() {
        super.open('overview/import')
        browser.waitForExist('.id-import-source-type')
    }

    get applyFilterBatchButton() {
        return util.element('.id-import-filter-apply')
    }

    get addAllButton() {
        return util.element('.id-import-add-all')
    }

    get clearFilterBatchButton() {
        return util.element('.id-import-filter-clear')
    }

    get filterBatchTextbox() {
        return util.element('.id-import-filter-batch')
    }

    get importButton() {
        return util.element('.id-import-import-button')
    }

    get parseDataButton() {
        return util.element('.id-import-parse-data')
    }

    get variantImportButton() {
        return util.element('.id-import-user-import-button')
    }

    getActiveImportTitle(idx) {
        browser.waitForExist(
            `.id-import-active-imports .import-job-list .list-item:nth-child(${idx}) .job-title`
        )
        return browser
            .element(
                `.id-import-active-imports .import-job-list .list-item:nth-child(${idx}) .job-title`
            )
            .getText()
    }

    getHistoryImportTitle(idx) {
        const selector = `import sectionbox:nth-child(2) > section.sectionbox.collapsed`
        console.log(browser.isExisting(selector))
        if (browser.isExisting(selector)) {
            browser.click(
                'import sectionbox:nth-child(2) > section.sectionbox.collapsed .sb-title-container'
            )
        }
        browser.waitForExist(
            `.id-import-import-history .import-job-list .list-item:nth-child(${idx}) .job-title`
        )
        return browser
            .element(
                `.id-import-import-history .import-job-list .list-item:nth-child(${idx}) .job-title`
            )
            .getText()
    }

    selectImportSource(type) {
        if (type === 'variants') {
            browser.element('.id-import-source-type label:nth-child(1)').click()
        } else if (type === 'sample') {
            browser.element('.id-import-source-type label:nth-child(2)').click()
        }
    }

    enterVariantData(data) {
        browser.element('.id-variant-data-input > textarea').setValue(data)
    }

    searchSample(term) {
        browser.element('.id-import-sample input').setValue(term)
        browser.waitForExist('.selector-optgroup')
    }

    selectSearchResult() {
        browser.keys('Enter')
    }

    toggleCustomGenePanel(toggle) {
        const selectorIdx = toggle ? 1 : 2
        browser.element(`.id-import-custom-panel label:nth-child(${selectorIdx})`).click()

        if (toggle) {
            browser.waitForExist('.id-import-filter-results .list-item')
        }
    }

    selectGenePanel(name) {
        browser.element('.id-import-genepanel-source').selectByVisibleText(name)
    }

    selectFilterMode(mode) {
        const selectors = {
            single: 1,
            batch: 2
        }
        browser.element(`.id-import-filter-mode label:nth-child(${selectors[mode]})`).click()
    }

    enterFilterTerm(text) {
        browser.element(`.id-import-filter-single`).setValue(text)
    }

    enterFilterBatchTerm(text) {
        this.filterBatchTextbox.setValue(text)
    }

    enterCustomGenePanelName(name) {
        browser.element(`.id-import-custom-panel-name`).setValue(name)
    }

    getFilterResultText() {
        return browser.element(`.id-import-filter-results-text`).getText()
    }

    getAddedText() {
        return browser.element(`.id-import-added-text`).getText()
    }

    addFilterResult(idx) {
        browser
            .element(
                `.id-import-filter-results .list-item:nth-child(${idx}) button.id-import-add-single`
            )
            .click()
    }

    getImportSummary() {
        return browser.element(`.id-import-summary`).getText()
    }
}

module.exports = Import
