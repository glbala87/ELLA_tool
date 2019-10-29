require('core-js/fn/object/entries')

let LoginPage = require('../pageobjects/loginPage')
let Import = require('../pageobjects/overview_import')

let loginPage = new LoginPage()
let importPage = new Import()

var failFast = require('jasmine-fail-fast')
jasmine.getEnv().addReporter(failFast.init())

describe('Import functionality', function() {
    beforeAll(() => {
        browser.resetDb()
    })
    it('import analysis from sample repository on custom gene panel', function() {
        loginPage.open()
        loginPage.selectFirstUser()

        importPage.open()
        importPage.selectImportSource('sample')

        // Mock service always returns 'TESTSAMPLE1',
        // so doesn't really matter
        importPage.searchSample('TESTSAMPLE1')
        importPage.selectSearchResult()

        importPage.toggleCustomGenePanel(true)

        importPage.enterCustomGenePanelName('MyPanel')

        importPage.selectGenePanel('HBOCUTV_v01')

        importPage.selectFilterMode('batch')

        importPage.enterFilterBatchTerm('BRCA1; BRCA2 CDH1 PALB2 IAMMISSING')
        importPage.applyFilterBatchButton.click()

        expect(importPage.filterBatchTextbox.getValue()).toBe('IAMMISSING')

        expect(importPage.getFilterResultText()).toBe('4 TRANSCRIPTS (4 GENES)')

        importPage.addAllButton.click()

        expect(importPage.getAddedText()).toBe('4 TRANSCRIPTS (4 GENES)')

        importPage.clearFilterBatchButton.click()

        importPage.selectFilterMode('single')

        importPage.enterFilterTerm('PTE') // PTEN
        expect(importPage.getFilterResultText()).toBe('1 TRANSCRIPTS (1 GENES)')

        importPage.addFilterResult(1)
        expect(importPage.getAddedText()).toBe('5 TRANSCRIPTS (5 GENES)')

        const panelName = `MyPanel_${new Date()
            .toISOString()
            .substr(2, 8)
            .replace(new RegExp('-', 'g'), '')}`

        expect(importPage.getImportSummary()).toBe(
            `Import Testsample1 on ${panelName} (custom) with 5 transcripts (5 genes).`
        )

        importPage.importButton.click()

        expect(importPage.getActiveImportTitle(1)).toBe(
            `Create new analysis from sample: Testsample1 (${panelName})`
        )
    })

    it('import analysis from variants', function() {
        importPage.selectImportSource('variants')
        importPage.enterVariantData(
            '-- TestSample01\nNM_000059.3:c.9732_9733insA (het)\nNM_000059.3(BRCA2):c.9732_9733insA (homo)'
        )

        importPage.parseDataButton.click()
        importPage.variantImportButton.click()
        expect(importPage.getActiveImportTitle(1)).toBe(
            'Create new analysis: TestSample01 (HBOC_v01)'
        )
    })
})
