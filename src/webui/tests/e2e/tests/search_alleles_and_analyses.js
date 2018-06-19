require('core-js/fn/object/entries')

let LoginPage = require('../pageobjects/loginPage')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let Search = require('../pageobjects/overview_search')

let loginPage = new LoginPage()
let analysisPage = new AnalysisPage()
let alleleSectionBox = new AlleleSectionBox()
let search = new Search()

var failFast = require('jasmine-fail-fast')
jasmine.getEnv().addReporter(failFast.init())

describe('Search functionality', function() {
    beforeAll(() => {
        browser.resetDb()
    })
    it('search for analyses', function() {
        loginPage.selectFirstUser()
        search.open()
        search.selectType('analyses')
        search.searchFreetext('brca')
        expect(search.getNumberOfAnalyses()).toBe(3)

        // Start an analysis from search
        search.selectFirstAnalysis()
        analysisPage.startButton.click()

        // Search for analysis by user
        search.open()
        search.selectType('analyses')
        browser.element('.id-select-user input').setValue('Hen')
        browser.waitForExist('.selector-optgroup')
        browser.keys('Enter')
        expect(search.getNumberOfAnalyses()).toBe(1)
    })

    it('search for variants', function() {
        // Search for variant using freetext
        search.open()
        search.selectType('variants')
        search.searchFreetext('c.1788')
        browser.element('.id-select-gene input').setValue('BRCA2')
        browser.waitForExist('.selector-optgroup')
        browser.keys('Enter')
        expect(search.getNumberOfAlleles()).toBe(1)

        // Classify variant as class 3
        search.selectFirstAllele()
        analysisPage.startButton.click()
        alleleSectionBox.classifyAs3()
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()

        // Allele assessment shows in search
        search.open()
        search.searchFreetext('c.1788')
        search.selectType('variants')
        search.searchFreetext('c.1788')
        browser.element('.id-select-gene input').setValue('BRCA2')
        browser.waitForExist('.selector-optgroup')
        browser.keys('Enter')
        expect(search.getNumberOfAlleles()).toBe(1)

        // Check that it has classification text
        browser.getText('*=CLASS 3')

        // Search for variant connected to gene and user
        search.searchFreetext('')

        browser.element('.id-select-user input').setValue('Hen')
        browser.waitForExist('.selector-optgroup')
        browser.keys('Enter')
        expect(search.getNumberOfAlleles()).toBe(1)

        browser.element('.id-select-user').click()
    })

    it('shows connected analyses', function() {
        search.open()
        search.searchFreetext('c.289')
        browser.element('.id-select-gene input').setValue('BRCA2')
        browser.waitForExist('.selector-optgroup')
        browser.keys('Enter')
        let analyses = search.getAnalysesForFirstAllele()
        expect(analyses.length).toBe(2)
    })
})
