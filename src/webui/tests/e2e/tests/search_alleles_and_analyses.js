require('core-js/fn/object/entries');

let LoginPage = require('../pageobjects/loginPage')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let Search = require('../pageobjects/overview_search')

let loginPage = new LoginPage()
let analysisPage = new AnalysisPage()
let alleleSectionBox = new AlleleSectionBox();
let search = new Search()

var failFast = require('jasmine-fail-fast');
jasmine.getEnv().addReporter(failFast.init());

describe('Search functionality', function () {

    beforeAll(() => {
        browser.resetDb();
    });
    it('search for analyses', function() {
        loginPage.selectFirstUser()
        search.open()
        search.searchFreetext('brca')
        expect(search.getNumberOfAnalyses()).toBe(3)

        // Start an analysis from search
        search.selectFirstAnalysis()
        analysisPage.startButton.click()

        // Search for analysis by user
        search.open()
        browser.element('.id-select-user .selector-input').click()
        browser.element('.id-select-user .selector-dropdown li:nth-child(6)').click()
        expect(search.getNumberOfAnalyses()).toBe(1)
    })


    it('search for variants', function () {
        // Search for variant using freetext
        search.open()
        search.searchFreetext("c.1788")
        expect(search.getNumberOfAlleles()).toBe(1)

        // This variant should be filtered out
        search.filterResults()
        expect(search.getNumberOfAlleles()).toBe(0)
        search.noFilterResults()
        expect(search.getNumberOfAlleles()).toBe(1)

        // Classify variant as class 3
        search.selectFirstAllele()
        analysisPage.startButton.click()
        alleleSectionBox.classifyAs3()
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click();

        // Allele assessment shows in search
        search.open()
        search.searchFreetext("c.1788")
        expect(search.getNumberOfAlleles()).toBe(1)
        search.filterResults()

        // Allele should now not be filtered (as it's a class 3 variant)
        expect(search.getNumberOfAlleles()).toBe(1)

        // Check that it has classification text
        browser.getText("*=CLASS 3")

        // Search for variant connected to gene and user
        search.searchFreetext('')

        browser.element('.id-select-user .selector-input').click()
        browser.element('.id-select-user .selector-dropdown li:nth-child(6)').click()
        expect(search.getNumberOfAlleles()).toBe(1)

        browser.element('.id-select-gene input').setValue("BRC")
        // Top element should now be BRCA2: select by pressing enter
        browser.keys("Enter")
        expect(search.getNumberOfAlleles()).toBe(1)

        browser.element('.id-select-user').click()
        expect(search.getNumberOfAlleles()).toBeGreaterThan(1)
    })

    it('shows connected analyses', function() {
        search.open()
        search.searchFreetext("c.289")
        let analyses = search.getAnalysesForFirstAllele()
        expect(analyses.length).toBe(2)
    })
});
