require('core-js/fn/object/entries')

/**
 * Performs interpretations for three samples and evaluate some references.
 * - Sample 1: interpret one round, set to review.
 * - Sample 1: check if interpretations from previous round is stored. Finalize the sample.
 * - Sample 2: check if variants common with sample 1 are already classified.
 *             change a variant that also exists in sample 3
 * - Sample 3: confirm that the changed classification in 2nd sample is carried
 *             over correctly, and that it's using the latest classification rather
 *             than the first one made as part of 1st sample.
 *
 *  For some alleles we have ExAC/gnomeAD data. For those we test that the data is present on page.
 */

let LoginPage = require('../pageobjects/loginPage')
let AddExcludedAllelesModal = require('../pageobjects/addExcludedModal')
let SampleSelectionPage = require('../pageobjects/overview_samples')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSidebar = require('../pageobjects/alleleSidebar')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let WorkLog = require('../pageobjects/workLog')
let CustomAnnotationModal = require('../pageobjects/customAnnotationModal')
let ReferenceEvalModal = require('../pageobjects/referenceEvalModal')
let checkAlleleClassification = require('../helpers/checkAlleleClassification')

let loginPage = new LoginPage()
let addExcludedAllelesModal = new AddExcludedAllelesModal()
let sampleSelectionPage = new SampleSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSidebar = new AlleleSidebar()
let alleleSectionBox = new AlleleSectionBox()
let workLog = new WorkLog()
let customAnnotationModal = new CustomAnnotationModal()
let referenceEvalModal = new ReferenceEvalModal()

const BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION = 'RE-EVALUATE'
const SAMPLE_ONE = 'HG002-Trio.Mendeliome_v01'
const TITLE_INTERPRETATION = ' • INTERPRETATION'
const TITLE_REVIEW = ' • REVIEW'

describe('Sample workflow', function() {
    console.log(
        'Starting test suite ' +
            "'Sample workflow' with a timeout of " +
            jasmine.DEFAULT_TIMEOUT_INTERVAL
    )

    beforeAll(() => {
        browser.resetDb()
    })

    function setFinalizationRequirements(
        allow_technical = false,
        allow_notrelevant = false,
        allow_unclassified = false,
        workflow_status = ['Review', 'Medical review']
    ) {
        let result = browser.psql(`
          UPDATE "user" SET config =
          '{ "workflows": { "analysis": { "finalize_requirements": {
              "allow_technical": ${allow_technical ? 'true' : 'false'},
              "allow_notrelevant": ${allow_notrelevant ? 'true' : 'false'},
              "allow_unclassified": ${allow_unclassified ? 'true' : 'false'},
              "workflow_status": ${JSON.stringify(workflow_status)}
              } } } }' WHERE username IN ('testuser4')
      `)
        expect(result).toEqual('UPDATE 1\n')
    }

    it('login as testuser4, preselected allele should be first snv in alleleSideBarList', function() {
        // Modify user config to allow finalization with classifying all variants

        loginPage.open()
        loginPage.loginAs('testuser4')
        browser.execute(`localStorage.clear()`) // Needs a proper URL, hence after login
        sampleSelectionPage.selectTopPending()

        expect(analysisPage.title).toBe(SAMPLE_ONE + TITLE_INTERPRETATION)
        analysisPage.startButton.click()
        let selectedAllele = alleleSidebar.getSelectedAllele()
        expect(selectedAllele).toBe('c.4958_4975dup')

        setFinalizationRequirements(true, true, true, ['Interpretation'])
        browser.refresh()
        expect(analysisPage.getFinalizePossible()).toBe(true)
    })

    // Store entered data for interpretation round 1 {c.1234A>C: ...}
    // Will be checked against in round two
    let expected_analysis_1_round_1 = {}
    let expected_analysis_2_round_1 = {}

    it('allows interpretation, classification and reference evaluation to be set to review', function() {
        setFinalizationRequirements(true, true, false)
        browser.refresh()
        expect(analysisPage.getFinalizePossible()).toBe(false)

        expect(analysisPage.title).toBe(SAMPLE_ONE + TITLE_INTERPRETATION)
        //analysisPage.startButton.click()

        cnvSelector = analysisPage.cnvSelector
        cnvSelector.waitForExist()
        cnvSelector.click()

        unclassifiedCnvs = alleleSidebar.countOfUnclassified()
        expect(unclassifiedCnvs).toBe(27)

        analysisPage.classificationTypeVisualButton.scrollIntoView({ block: 'center' })
        analysisPage.classificationTypeVisualButton.click()
        //g.27776481_135255460del
        alleleSidebar.quickSetTechnical('g.27776481_135255460del')

        let selected_allele = alleleSidebar.getSelectedAllele()
        expect(alleleSidebar.isAlleleInTechnical(selected_allele)).toBe(true)
        alleleSidebar.setTechnicalComment('g.27776481_135255460del', 'TECHNICAL_ROUND_1')
        expected_analysis_1_round_1[selected_allele] = {
            technical: true,
            analysisComment: 'TECHNICAL_ROUND_1'
        }

        analysisPage.classificationTypeQuickButton.scrollIntoView({ block: 'center' })
        analysisPage.classificationTypeQuickButton.click()
        alleleSidebar.quickSetNotRelevant('g.12951329_88076640del')
        selected_allele = alleleSidebar.getSelectedAllele()
        expect(alleleSidebar.isAlleleInNotRelevant(selected_allele)).toBe(true)
        alleleSidebar.setNotRelevantComment('g.12951329_88076640del', 'NOTRELEVANT_ROUND_1')
        expected_analysis_1_round_1[selected_allele] = {
            notRelevant: true,
            analysisComment: 'NOTRELEVANT_ROUND_1'
        }

        analysisPage.classificationTypeQuickButton.scrollIntoView({ block: 'center' })
        alleleSidebar.quickClassNP('g.22454833_65164799dup_tandem')
        selected_allele = alleleSidebar.getSelectedAllele()
        expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true)
        alleleSidebar.setEvaluationComment('g.22454833_65164799dup_tandem', 'EVALUATION_ROUND_1')
        expected_analysis_1_round_1[selected_allele] = {
            classification: 'NP',
            evaluation: 'EVALUATION_ROUND_1'
        }

        // Classify rest using 'Full' classification view
        analysisPage.classificationTypeFullButton.scrollIntoView({ block: 'center' })
        analysisPage.classificationTypeFullButton.click()

        testAlleles = [
            'g.140039852_140039910del',
            'g.119964016_119964075del',
            'g.60694533_60695080del'
        ]
        for (let idx = 0; idx < testAlleles.length; idx++) {
            // unclassified count to avoid timing issue later
            const numUnclassified = alleleSidebar.countOfUnclassified()

            alleleSidebar.selectUnclassifiedAllele(testAlleles[idx])
            selected_allele = alleleSidebar.getSelectedAllele(testAlleles[idx])
            console.log(`Classifying variant: ${selected_allele} in loop with idx=${idx}`)

            if (idx == testAlleles.length - 1) {
                alleleGene = alleleSidebar.getSelectedGene()
                expect(alleleGene).toBe('BCL11A')
                geneComment = `GENE COMMENT FOR ${alleleGene}`
                analysisPage.setGeneComment(geneComment)
                expect(analysisPage.getGeneComment()).toBe(geneComment)
            }

            // Add attachment
            expect(alleleSectionBox.getNumberOfAttachments()).toEqual(0)
            analysisPage.addAttachment()
            expect(alleleSectionBox.getNumberOfAttachments()).toEqual(1)

            // // Add external annotation
            console.log('Adding custom annotation')
            alleleSectionBox.addExternalBtn.click()
            customAnnotationModal.setExternalAnnotationText('structural variant')
            customAnnotationModal.saveBtn.click()
            customAnnotationModal.waitForClose()
            expect(alleleSectionBox.getExternalOtherValue()).toEqual('structural variant')

            // Add prediction annotation
            console.log('Adding prediction annotation')
            alleleSectionBox.addPredictionBtn.click()
            customAnnotationModal.setPredictionAnnotation(4, 1) // DOMAIN: CRITICAL FUNCTIONAL DOMAIN
            customAnnotationModal.saveBtn.click()
            customAnnotationModal.waitForClose()
            expect(alleleSectionBox.getPredictionOtherAnnotation()).toEqual('Domain:')
            expect(alleleSectionBox.getPredictionOtherValue()).toEqual('critical_domain')

            // Set comments/classification
            console.log('Adding comments')
            alleleSectionBox.setClassificationComment('EVALUATION_ROUND1')
            analysisPage.saveButton.click()
            alleleSectionBox.setFrequencyComment('FREQUENCY_ROUND1')
            analysisPage.saveButton.click()
            alleleSectionBox.setPredictionComment('PREDICTION_ROUND1')
            analysisPage.saveButton.click()
            alleleSectionBox.setExternalComment('EXTERNAL_ROUND1')
            analysisPage.saveButton.click()

            alleleSectionBox.setReportComment('REPORT_ROUND1 &~øæå')

            console.log('Adding ACMG codes')
            analysisPage.addAcmgCode('benign', 'BP2', 'BP2_ACMG_ROUND_1')
            analysisPage.addAcmgCode('pathogenic', 'PS2', 'PS2_ACMG_ROUND_1', -2) // Adjust down to PPxPS2
            analysisPage.addAcmgCode('pathogenic', 'PS1', 'PS1_ACMG_ROUND_1', 1) // Adjust up to PVSxPS1

            console.log('Setting class ' + (idx + 1))
            alleleSectionBox.classSelection.selectByVisibleText(`Class ${idx + 1}`)

            // needs a moment for change to propagate
            browser.waitUntil(
                () => alleleSidebar.countOfUnclassified(selected_allele) < numUnclassified,
                {
                    timeout: 1000
                }
            )
            if (idx == 0) {
                expected_analysis_1_round_1[' g.27776481_135255460del'] = {
                    technical: true,
                    analysisComment: 'TECHNICAL_ROUND_1'
                }

                // Check that we cannot finalize, as we're only in "Interpretation" workflow status
                expect(alleleSectionBox.finalizeBtn.isEnabled()).toBe(false)

                expected_analysis_1_round_1 = {
                    'g.27776481_135255460del': {
                        technical: true,
                        analysisComment: 'TECHNICAL_ROUND_1'
                    },
                    'g.12951329_88076640del': {
                        notRelevant: true,
                        analysisComment: 'NOTRELEVANT_ROUND_1'
                    },
                    'g.216185304_216198475del': {
                        classification: 'NP',
                        evaluation: 'EVALUATION_ROUND_1'
                    }
                }
            }
        }
    })
})
