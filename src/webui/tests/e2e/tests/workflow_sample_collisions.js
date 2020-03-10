require('core-js/fn/object/entries')

/**
 * Checks that collision warning is displayed when starting interpretation with variants that overlap another
 * ongoing interpretation
 */

let LoginPage = require('../pageobjects/loginPage')
let SampleSelectionPage = require('../pageobjects/overview_samples')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSidebar = require('../pageobjects/alleleSidebar')

let loginPage = new LoginPage()
let analysesSelectionPage = new SampleSelectionPage()
let alleleSectionBox = new AlleleSectionBox()
let analysisPage = new AnalysisPage()
let alleleSidebar = new AlleleSidebar()

var failFast = require('jasmine-fail-fast')

describe('Sample workflow', function() {
    beforeAll(() => {
        browser.resetDb()
    })

    it('gives warning when starting a sample with variants that overlap with other ongoing sample', function() {
        // sample 1
        loginPage.open()
        loginPage.loginAs('testuser1')
        analysesSelectionPage.selectTopPending()
        analysisPage.startButton.click()

        // sample 2
        loginPage.open()
        loginPage.loginAs('testuser2')
        analysesSelectionPage.selectTopPending()
        alleleSidebar.selectUnclassifiedAlleleByIdx(3)
        expect(alleleSectionBox.alleleWarningText).toEqual(
            'This variant is currently being worked on by Henrik Ibsen in another analysis: brca_e2e_test01.HBOCUTV_v01.'
        )
    })

    it('gives warning when variant is classified by different user group', function() {
        // sample 1
        loginPage.open()
        loginPage.loginAs('testuser1')
        analysesSelectionPage.selectTopPending()
        analysisPage.startButton.click()

        // Classify NM_000059.3:c.10G>T as 5
        alleleSectionBox.classifyAs5()
        alleleSectionBox.finalize()
        browser.pause(500) // Wait for allele to be processed in backend

        browser.psql(`UPDATE alleleassessment SET usergroup_id = 2`)
        browser.refresh()
        alleleSidebar.selectFirstClassified()
        expect(alleleSectionBox.alleleWarningText).toEqual(
            `This variant's existing classification was performed by a different user group: testgroup02.`
        )
    })
})
