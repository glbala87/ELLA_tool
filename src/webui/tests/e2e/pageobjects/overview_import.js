var Page = require('./page')
var util = require('./util')

class Import extends Page {
    open() {
        super.open('overview/import')
        $('.id-import-source-type').waitForExist()
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
        $(
            `.id-import-active-imports .import-job-list .list-item:nth-child(${idx}) .job-title`
        ).waitForExist()
        return $(
            `.id-import-active-imports .import-job-list .list-item:nth-child(${idx}) .job-title`
        ).getText()
    }

    getHistoryImportTitle(idx) {
        const selector = `import sectionbox:nth-child(2) > section.sectionbox.collapsed`
        if ($(selector).isExisting()) {
            $(
                'import sectionbox:nth-child(2) > section.sectionbox.collapsed .sb-title-container'
            ).click()
        }
        $(
            `.id-import-import-history .import-job-list .list-item:nth-child(${idx}) .job-title`
        ).waitForExist()
        return $(
            `.id-import-import-history .import-job-list .list-item:nth-child(${idx}) .job-title`
        ).getText()
    }

    selectImportSource(type) {
        if (type === 'variants') {
            $('.id-import-source-type label:nth-child(1)').click()
        } else if (type === 'sample') {
            $('.id-import-source-type label:nth-child(2)').click()
        }
    }

    enterVariantData(data) {
        $('.id-variant-data-input > textarea').setValue(data)
    }

    searchSample(term) {
        $('.id-import-sample input').setValue(term)
        $('.selector-optgroup').waitForExist()
    }

    selectSearchResult() {
        browser.keys('Enter')
    }

    toggleCustomGenePanel(toggle) {
        const selectorIdx = toggle ? 1 : 2
        $(`.id-import-custom-panel label:nth-child(${selectorIdx})`).click()

        if (toggle) {
            $('.id-import-filter-results .list-item').waitForExist()
        }
    }

    selectGenePanel(name) {
        $('.id-import-genepanel-source').selectByVisibleText(name)
    }

    selectFilterMode(mode) {
        const selectors = {
            single: 1,
            batch: 2
        }
        $(`.id-import-filter-mode label:nth-child(${selectors[mode]})`).click()
    }

    enterFilterTerm(text) {
        $(`.id-import-filter-single`).setValue(text)
    }

    enterFilterBatchTerm(text) {
        this.filterBatchTextbox.setValue(text)
    }

    enterCustomGenePanelName(name) {
        $(`.id-import-custom-panel-name`).setValue(name)
    }

    getFilterResultText() {
        return $(`.id-import-filter-results-text`).getText()
    }

    getAddedText() {
        return $(`.id-import-added-text`).getText()
    }

    addFilterResult(idx) {
        $(
            `.id-import-filter-results .list-item:nth-child(${idx}) button.id-import-add-single`
        ).click()
    }

    getImportSummary() {
        return $(`.id-import-summary`).getText()
    }
}

module.exports = Import
