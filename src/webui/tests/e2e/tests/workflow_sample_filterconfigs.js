require('core-js/fn/object/entries')

/**
 * Open an analysis
 * 1. Cycle through two different filter configs
 * 2. Start analysis with a strict filter config (A)
 * 3. Include two alleles: One that will be filtered by both filter configs, one that will only be filtered A.
 *    (Check that both show as manually included in allele sidebar)
 * 4. Send analysis to review
 * 5. Second user starts review.
 * 6. Select filter config B. Check that one of the two alleles show as manually included (the other would not be filtered by this)
 * 7. Check that excluded alleles shows only one included allele.
 * 8. Send analysis to review.
 * 9. Disable filter config A
 * 10.
 * Finalize two analyses, checking the interpretation rounds for the finished analyses:
 * 1. Sample 1, all classified as 1, set to review,
 * 2. Sample 1, , all classified as 2, finalization
 * 3. Sample 2: alleles overlap with previous sample 1, all classified as class U, finalize
 * 4. Open sample 1 (with two rounds). Check the rounds are different
 * 5. Open sample 2 (with one round). Check that some variants had an existing classification
 */

let LoginPage = require('../pageobjects/loginPage')
let SampleSelection = require('../pageobjects/overview_samples')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSidebar = require('../pageobjects/alleleSidebar')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let AddExcludedModal = require('../pageobjects/addExcludedModal')
let failFast = require('jasmine-fail-fast')

let loginPage = new LoginPage()
let overview = new SampleSelection(false)
let analysisPage = new AnalysisPage()
let alleleSidebar = new AlleleSidebar()
let alleleSectionBox = new AlleleSectionBox()
let addExcludedModal = new AddExcludedModal()

jasmine.getEnv().addReporter(failFast.init())

describe('Dynamic filter configs ', function() {
    beforeAll(() => {
        browser.resetDb()

        // console.log(browser.psql('SELECT * from filterconfig where active=true'))
        console.log(browser.psql('UPDATE filterconfig SET active=false;'))

        console.log(
            browser.psql(
                `INSERT INTO filterconfig
                (
                    name,
                    usergroup_id,
                    "order",
                    requirements,
                    active,
                    filterconfig
                )
                VALUES
                (
                    'FC_A',
                    1,
                    10,
                    '[]',
                    true,
                    '{
                        "filters":
                        [
                            {
                                "name": "consequence",
                                "config": {
                                    "consequences": ["stop_gained"]
                                }
                            }
                        ]
                    }
                ');`
            )
        )

        console.log(
            browser.psql(
                `INSERT INTO filterconfig
                (
                    name,
                    usergroup_id,
                    "order",
                    requirements,
                    active,
                    filterconfig
                )
                VALUES
                (
                    'FC_B',
                    1,
                    11,
                    '[]',
                    true,
                    '{
                        "filters":
                        [
                            {
                                "name": "consequence",
                                "config": {
                                    "consequences": ["synonymous_variant"]
                                }
                            },
                            {
                                "name": "region",
                                "config": {
                                    "splice_region": [0,0]
                                }
                            }
                        ]
                    }
                ');`
            )
        )
        browser.psql(
            `UPDATE usergroup SET config=jsonb_set(config, '{overview,views}', '["analyses", "import"]') WHERE id=1;`
        )

        // Create filter configs in db
    })

    const availableFilterConfigs = ['FC_A', 'FC_B']

    it('cycle through available filter configs, include alleles', () => {
        // brca_e2e_test02.HBOCUTV_v01
        loginPage.selectFirstUser()
        overview.open()
        overview.selectPending(2)
        expect(alleleSidebar.getFilterConfigCount()).toEqual(2)
        analysisPage.startButton.click()

        // Include alleles from both filter configs
        alleleSidebar.selectFilterConfig(2)
        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_B')
        expect(alleleSidebar.countOfUnclassified()).toEqual(3)
        alleleSidebar.addExcludedButton.click()
        addExcludedModal.includeAllele(1)
        addExcludedModal.closeBtn.click()
        expect(alleleSidebar.countOfUnclassified()).toEqual(4)

        alleleSidebar.selectFilterConfig(1)
        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_A')
        expect(alleleSidebar.countOfUnclassified()).toEqual(2)
        alleleSidebar.addExcludedButton.click()
        addExcludedModal.selectCategory('CONSEQUENCE')
        addExcludedModal.includeAllele(1)
        addExcludedModal.includeAllele(1)
        addExcludedModal.closeBtn.click()
        expect(alleleSidebar.countOfUnclassified()).toEqual(4)

        // Check that different filter configs respect their respective manually included alleles
        expect(alleleSidebar.addExcludedButtonText).toEqual('2/3')
        expect(browser.elements('.manually-added').elements('span=I').value.length).toEqual(2)
        alleleSidebar.addExcludedButton.click()
        expect(addExcludedModal.numberOfIncluded).toEqual(2)
        addExcludedModal.closeBtn.click()

        alleleSidebar.selectFilterConfig(2)
        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_B')
        expect(alleleSidebar.addExcludedButtonText).toEqual('1/2')
        expect(browser.elements('.manually-added').elements('span=I').value.length).toEqual(1)
        alleleSidebar.addExcludedButton.click()
        expect(addExcludedModal.numberOfIncluded).toEqual(1)
        addExcludedModal.closeBtn.click()

        alleleSidebar.selectFilterConfig(1)
        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_A')
        expect(alleleSidebar.addExcludedButtonText).toEqual('2/3')
        expect(browser.elements('.manually-added').elements('span=I').value.length).toEqual(2)
        alleleSidebar.addExcludedButton.click()
        expect(addExcludedModal.numberOfIncluded).toEqual(2)
        addExcludedModal.closeBtn.click()

        // Create state
        let i = 0
        while (alleleSidebar.countOfUnclassified()) {
            alleleSidebar.selectFirstUnclassified()
            // alleleSectionBox.setClassificationComment('EVALUATION_ROUND1')
            // analysisPage.saveButton.click()
            // alleleSectionBox.setFrequencyComment('FREQUENCY_ROUND1')
            // analysisPage.saveButton.click()
            // alleleSectionBox.setPredictionComment('PREDICTION_ROUND1')
            // analysisPage.saveButton.click()
            // alleleSectionBox.setExternalComment('EXTERNAL_ROUND1')
            // analysisPage.saveButton.click()
            // alleleSectionBox.setReportComment('REPORT_ROUND1')
            // analysisPage.saveButton.click()
            alleleSectionBox.classSelection.selectByVisibleText(`Class ${i + 1}`)
            analysisPage.saveButton.click()
            i++
        }
        analysisPage.finishButton.click()
        analysisPage.markReviewButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('select different filter config, check included alleles', () => {
        overview.open()
        overview.selectTopReview()

        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_A')
        expect(alleleSidebar.addExcludedButtonText).toEqual('2/3')
        expect(browser.elements('.manually-added').elements('span=I').value.length).toEqual(2)
        alleleSidebar.addExcludedButton.click()
        expect(addExcludedModal.numberOfIncluded).toEqual(2)
        addExcludedModal.closeBtn.click()

        alleleSidebar.selectFilterConfig(2)
        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_B')
        expect(alleleSidebar.addExcludedButtonText).toEqual('1/2')
        expect(browser.elements('.manually-added').elements('span=I').value.length).toEqual(1)
        alleleSidebar.addExcludedButton.click()
        expect(addExcludedModal.numberOfIncluded).toEqual(1)
        addExcludedModal.closeBtn.click()

        // Filter config dropdown disabled for historical data
        analysisPage.chooseRound(1)
        expect(alleleSidebar.selectFilterConfigDropdown().isEnabled()).toBe(false)
        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_A')
        expect(alleleSidebar.addExcludedButtonText).toEqual('2/3')
        expect(browser.elements('.manually-added').elements('span=I').value.length).toEqual(2)
        alleleSidebar.addExcludedButton.click()
        expect(addExcludedModal.numberOfIncluded).toEqual(2)
        addExcludedModal.closeBtn.click()

        analysisPage.chooseRound(2)
        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_A')
        analysisPage.startButton.click()
        alleleSidebar.selectFilterConfig(2)
        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_B')
        expect(alleleSidebar.countOfUnclassified()).toEqual(1)

        alleleSidebar.selectFirstUnclassified()
        // alleleSectionBox.setClassificationComment('FC_B ROUND2')
        // analysisPage.saveButton.click()
        // alleleSectionBox.setFrequencyComment('FC_B ROUND2')
        // analysisPage.saveButton.click()
        // alleleSectionBox.setPredictionComment('FC_B ROUND2')
        // analysisPage.saveButton.click()
        // alleleSectionBox.setExternalComment('FC_B ROUND2')
        // analysisPage.saveButton.click()
        // alleleSectionBox.setReportComment('FC_B ROUND2')
        // analysisPage.saveButton.click()
        alleleSectionBox.classSelection.selectByVisibleText('Class 5')
        analysisPage.saveButton.click()

        alleleSidebar.addExcludedButton.click()
        addExcludedModal.excludeAllele(1)
        addExcludedModal.selectCategory('CONSEQUENCE')
        addExcludedModal.includeAllele(1)
        addExcludedModal.closeBtn.click()

        analysisPage.finishButton.click()
        analysisPage.markReviewButton.click()
        analysisPage.modalFinishButton.click()

        // Check state
    })

    it('check that only one filter config available, check history', () => {
        // disable filter config for third round
        browser.psql(`UPDATE filterconfig SET active=false WHERE name='FC_B';`)
        overview.open()
        overview.selectTopReview()

        // Even thoug previous round was used FC_B, this should now use FC_A as FC_B is disabled
        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_A')
        analysisPage.chooseRound(2)
        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_B')
        expect(alleleSidebar.selectFilterConfigDropdown().isEnabled()).toBe(false)
        analysisPage.chooseRound(1)
        expect(alleleSidebar.selectedFilterConfigName).toEqual('FC_A')
        expect(alleleSidebar.selectFilterConfigDropdown().isEnabled()).toBe(false)

        // First filter config selected
    })
})
