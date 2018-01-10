var Page = require('./page');

const SELECTOR_SEARCH = ".id-search"

const SECTION_EXPAND_SELECTOR  = " header .sb-title-container";

class Search extends Page {

    open() {
        super.open('overview/');
        browser.waitForExist(SELECTOR_SEARCH)
        if (browser.element(SELECTOR_SEARCH+" .collapsed")) {
            browser.click(SELECTOR_SEARCH+SECTION_EXPAND_SELECTOR)
        }
    }

    searchFreetext(searchText) {
        browser.element('.id-search-freetext').setValue(searchText)
    }

    getNumberOfAlleles() {
        const groupSelector = `.id-search .allele-list a`;
        if (!browser.isExisting(groupSelector)) {
            return 0;
        } else {
            return browser.elements(groupSelector).value.length
        }
    }

    getNumberOfAnalyses() {
        const groupSelector = '.id-search .analysis-list a';
        if (!browser.isExisting(groupSelector)) {
            return 0;
        } else {
            return browser.elements(groupSelector).value.length
        }
    }

    filterResults() {
        browser.click('label*=Yes')
    }

    noFilterResults() {
        browser.click('label*=No')
    }

    selectFirstAllele() {
        browser.click('.id-search .allele-list:nth-child(1)')
    }

    selectFirstAnalysis() {
        browser.click('.id-search .analysis-list:nth-child(1)')
    }

    getAnalysesForFirstAllele() {
        browser.click('.id-search .allele-list:nth-child(1) .allele-extras button')
        browser.click('button.red')
        let analyses = browser.getText('.modal-content .analysis-list .id-analysis-name')
        if (typeof a === 'string') {
            return [analyses]
        } else {
            return analyses;
        }
    }
}

module.exports = Search;