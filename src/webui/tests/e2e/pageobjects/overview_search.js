var Page = require('./page')

const SELECTOR_SEARCH = '.id-search'

const SECTION_EXPAND_SELECTOR = ' header .sb-title-container'
const ALLELE_RESULT_SELECTOR = '.id-search .allele-list a'
const ANALYSIS_RESULT_SELECTOR = '.id-search .analysis-list a'

class Search extends Page {
    open() {
        super.open('overview/')
        $(SELECTOR_SEARCH).waitForExist()
        if ($(SELECTOR_SEARCH + ' .collapsed').isExisting()) {
            $(SELECTOR_SEARCH + SECTION_EXPAND_SELECTOR).click()
        }
    }

    user(username) {
        $('.id-select-user input').setValue(username)
        $('.selector-optgroup').waitForExist()
    }
    gene(genesymbol) {
        $('.id-select-gene input').setValue('BRCA2')
        $('.selector-optgroup').waitForExist()
    }

    runSearch() {
        browser.keys('Enter')
    }

    selectType(type) {
        if (type === 'variants') {
            $('.id-search-type:nth-child(1)').click()
        } else if (type === 'analyses') {
            $('.id-search-type:nth-child(2)').click()
        }
    }

    searchFreetext(searchText) {
        $('.id-search-freetext').setValue(searchText)
    }

    getNumberOfAlleles(shouldHaveResults) {
        if (shouldHaveResults) {
            $(ALLELE_RESULT_SELECTOR).waitForExist()
        }
        if (!$(ALLELE_RESULT_SELECTOR).isExisting()) {
            return 0
        } else {
            return $$(ALLELE_RESULT_SELECTOR).length
        }
    }

    getNumberOfAnalyses(shouldHaveResults) {
        if (shouldHaveResults) {
            $(ANALYSIS_RESULT_SELECTOR).waitForExist()
        }
        if (!$(ANALYSIS_RESULT_SELECTOR).isExisting()) {
            return 0
        } else {
            return $$(ANALYSIS_RESULT_SELECTOR).length
        }
    }

    filterResults() {
        $('label*=Yes').click()
    }

    noFilterResults() {
        $('label*=No').click()
    }

    selectFirstAllele() {
        $('.id-search .allele-list:nth-child(1)').click()
    }

    selectFirstAnalysis() {
        $('.id-search .analysis-list:nth-child(1)').click()
    }

    getAnalysesForFirstAllele() {
        $('.id-search .allele-list:nth-child(1) .allele-extras button').click()
        $('button.red').click()
        $('.modal-content .analysis-list').waitForExist()
        let analyses = $$('.modal-content .analysis-list .id-analysis-name')
        return analyses.map((a) => a.getText())
    }
}

module.exports = Search
