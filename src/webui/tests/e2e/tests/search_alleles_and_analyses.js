const LoginPage = require('../pageobjects/loginPage')
const AnalysisPage = require('../pageobjects/analysisPage')
const AlleleSectionBox = require('../pageobjects/alleleSectionBox')
const Search = require('../pageobjects/overview_search')
const SampleSelectionPage = require('../pageobjects/overview_samples')

const loginPage = new LoginPage()
const analysisPage = new AnalysisPage()
const alleleSectionBox = new AlleleSectionBox()
const search = new Search()
const analysesSelectionPage = new SampleSelectionPage()

var failFast = require('jasmine-fail-fast')

describe('Search functionality', function() {
    beforeAll(() => {
        browser.resetDb()
    })

    it('search for analyses', function() {
        loginPage.open()
        loginPage.loginAs('testuser1')
        search.open()
        search.selectType('analyses')
        search.searchFreetext('brca')
        expect(search.getNumberOfAnalyses(true)).toBe(4)
        // Start an analysis from search
        search.selectFirstAnalysis()
        analysisPage.startButton.click()

        // Search for analysis by user
        search.open()
        search.selectType('analyses')
        search.user('Hen')
        search.runSearch()
        expect(search.getNumberOfAnalyses(true)).toBe(1)
    })

    it('search for variants', function() {
        // Search for variant using freetext
        search.open()
        search.selectType('variants')
        search.searchFreetext('c.1788')
        search.gene('BRCA2')
        search.runSearch()
        expect(search.getNumberOfAlleles(true)).toBe(1)

        // Classify variant as class 3
        search.selectFirstAllele()
        analysisPage.startButton.click()
        alleleSectionBox.classifyAs3()
        alleleSectionBox.finalize()
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()

        // Allele assessment shows in search
        search.open()
        search.searchFreetext('c.1788')
        search.selectType('variants')
        search.searchFreetext('c.1788')
        search.gene('BRCA2')
        search.runSearch()
        expect(search.getNumberOfAlleles(true)).toBe(1)

        // Check that it has classification text
        $('*=CLASS 3').getText()

        // Search for variant connected to gene and user
        search.searchFreetext('')

        search.user('Hen')
        search.runSearch()
        expect(search.getNumberOfAlleles(true)).toBe(1)

        $('.id-select-user').click()
    })

    it('shows connected analyses', function() {
        search.open()
        search.searchFreetext('c.289')
        search.gene('BRCA2')
        search.runSearch()
        let analyses = search.getAnalysesForFirstAllele()
        expect(analyses).toEqual([
            'brca_e2e_test01.HBOCUTV_v01.0 HTS',
            'brca_e2e_test02.HBOCUTV_v01.0 HTS'
        ])
    })

    it('filter analyses', function() {
        // set dates for dateRange test
        browser.psql(
            `UPDATE analysis
            SET date_requested = CURRENT_TIMESTAMP - interval '3 weeks'
            WHERE name = 'brca_e2e_test01.HBOCUTV_v01.0';`
        )
        // check that date_deposited is correctly fallen back to if no date_requested is set
        browser.psql(
            `UPDATE analysis
            SET date_requested = NULL,
                date_deposited = CURRENT_TIMESTAMP - interval '6 months'
            WHERE name = 'brca_e2e_test02.HBOCUTV_v01.0';`
        )
        // add review comment
        browser.psql(
            `INSERT INTO interpretationlog (
                analysisinterpretation_id,
                user_id,
                date_created,
                review_comment
            ) VALUES (
                (
                    SELECT ai.id
                    FROM analysisinterpretation AS ai
                    JOIN analysis AS an
                    ON an.id = ai.analysis_id
                    WHERE name = 'brca_e2e_test03.HBOCUTV_v01.0'
                ),
                1,
                current_timestamp,
                'TEST'
            );`
        )
        // set Sanger technology
        browser.psql(
            `UPDATE sample SET sample_type = 'Sanger' WHERE identifier = 'brca_e2e_test03';`
        )
        console.log(`Finished updating analyses for filter test`)

        // check initial data is as expected
        analysesSelectionPage.open()
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(4)
        // check name filter
        analysesSelectionPage.filterAnalysisName('test02')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(1)

        // check clear filter
        analysesSelectionPage.filterClear()
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(4)

        // test multiple priorities
        analysesSelectionPage.toggleFilterPriority('normal')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(4)
        analysesSelectionPage.toggleFilterPriority('urgent')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(4)
        analysesSelectionPage.toggleFilterPriority('normal')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(0)

        // test review comment
        analysesSelectionPage.filterClear()
        analysesSelectionPage.filterReviewComment('*')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(1)
        analysesSelectionPage.filterReviewComment('TES')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(1)
        analysesSelectionPage.filterReviewComment('TESLA')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(0)

        // test tech
        analysesSelectionPage.filterClear()
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(4)
        analysesSelectionPage.toggleFilterTechnology('HTS')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(3)
        analysesSelectionPage.toggleFilterTechnology('Sanger')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(4)
        analysesSelectionPage.toggleFilterTechnology('HTS')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(1)

        // test dateRange
        analysesSelectionPage.filterClear()
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(4)
        analysesSelectionPage.filterDateRange('lt:-7:d')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(2)
        analysesSelectionPage.filterDateRange('lt:-1:m')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(3)
        analysesSelectionPage.filterDateRange('ge:-3:m')
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(1)
        analysesSelectionPage.filterClear()
        expect(analysesSelectionPage.filteredAnalyses.length).toBe(4)
    })
})
