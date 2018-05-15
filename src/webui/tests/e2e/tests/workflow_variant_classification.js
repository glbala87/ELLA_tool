require('core-js/fn/object/entries')

/**
 * Performs interpretations a single variant
 */

let LoginPage = require('../pageobjects/loginPage')
let VariantSelectionPage = require('../pageobjects/overview_variants')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let CustomAnnotationModal = require('../pageobjects/customAnnotationModal')
let ReferenceEvalModal = require('../pageobjects/referenceEvalModal')
let checkAlleleClassification = require('../helpers/checkAlleleClassification')
let failFast = require('jasmine-fail-fast')

let loginPage = new LoginPage()
let variantSelectionPage = new VariantSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSectionBox = new AlleleSectionBox()
let customAnnotationModal = new CustomAnnotationModal()
let referenceEvalModal = new ReferenceEvalModal()

jasmine.getEnv().addReporter(failFast.init())

const OUR_VARIANT = 'c.581G>A'

describe(`Variant workflow (using ${OUR_VARIANT})`, function() {
    beforeAll(() => {
        browser.resetDb()
    })

    // Update expectations as we do interpretations in the UI
    let interpretation_expected_values = {}

    it('allows interpretation, classification and reference evaluation to be set to review', function() {
        loginPage.selectFirstUser()
        variantSelectionPage.selectPending(5)
        analysisPage.startButton.click()

        alleleSectionBox.classifyAsU()

        // Evaluate one reference
        let referenceTitle = alleleSectionBox.evaluateReference(1)
        console.log(`Evaluating reference ${referenceTitle}`)
        referenceEvalModal.setRelevance(1)
        referenceEvalModal.setComment('REFERENCE_EVAL_ROUND1')

        referenceEvalModal.saveBtn.click()
        referenceEvalModal.saveBtn.waitForExist(1000, true) // Wait for modal to close

        expect(alleleSectionBox.getReferenceComment(1)).toEqual('REFERENCE_EVAL_ROUND1')

        // Add external annotation
        alleleSectionBox.addExternalBtn.click()
        customAnnotationModal.setExternalAnnotation(3, 'Pathogenic') // LOVD IARC HCI
        customAnnotationModal.saveBtn.click()
        expect(alleleSectionBox.getExternalOtherAnnotation()).toEqual('LOVD IARC HCI:')
        expect(alleleSectionBox.getExternalOtherValue()).toEqual('pathogenic')

        // Add prediction annotation
        alleleSectionBox.addPredictionBtn.click()
        customAnnotationModal.setPredictionAnnotation(1, 2) // Ortholog conservation: Non-conserved
        customAnnotationModal.saveBtn.click()
        expect(alleleSectionBox.getPredictionOtherAnnotation()).toEqual('Ortholog conservation:')
        expect(alleleSectionBox.getPredictionOtherValue()).toEqual('non-conserved')

        // Set comments/classification
        alleleSectionBox.setClassificationComment('EVALUATION_ROUND1')
        analysisPage.saveButton.click()
        alleleSectionBox.setFrequencyComment('FREQUENCY_ROUND1')
        analysisPage.saveButton.click()
        alleleSectionBox.setPredictionComment('PREDICTION_ROUND1')
        analysisPage.saveButton.click()
        alleleSectionBox.setExternalComment('EXTERNAL_ROUND1')
        analysisPage.saveButton.click()
        alleleSectionBox.setReportComment('REPORT_ROUND1')
        browser.click('body') // a trick to unfocus the above report comment

        alleleSectionBox.classificationCommentElement.scroll()

        analysisPage.addAcmgCode('benign', 'BP2', 'BP2_ACMG_ROUND_1', 1) // Adjust up to BSxBP2
        analysisPage.addAcmgCode('pathogenic', 'PS2', 'PS2_ACMG_ROUND_1')
        analysisPage.addAcmgCode('pathogenic', 'PM1', 'PM1_ACMG_ROUND_1', 2) // Adjust up to PVSxPM1
        alleleSectionBox.classSelection.selectByVisibleText('Class 1')

        interpretation_expected_values = {
            OUR_VARIANT: {
                references: {
                    '1': {
                        relevance: 'Yes',
                        comment: 'REFERENCE_EVAL_ROUND1'
                    }
                },
                customAnnotation: {
                    external: {
                        'LOVD_genomed_China-BRCA2': 'pathogenic'
                    },
                    prediction: {
                        ortholog_conservation: 'non-conserved'
                    }
                },
                evaluation: 'EVALUATION_ROUND1',
                frequency: 'FREQUENCY_ROUND1',
                prediction: 'PREDICTION_ROUND1',
                external: 'EXTERNAL_ROUND1',
                report: 'REPORT_ROUND1',
                classification: '1',
                acmg: {
                    '1': {
                        code: 'BSxBP2',
                        comment: 'BP2_ACMG_ROUND_1'
                    },
                    '2': {
                        code: 'PS2',
                        comment: 'PS2_ACMG_ROUND_1'
                    },
                    '3': {
                        code: 'PVSxPM1',
                        comment: 'PM1_ACMG_ROUND_1'
                    }
                }
            }
        }

        alleleSectionBox.reviewCommentElement.setValue('REVIEW_COMMENT_ROUND1')
        analysisPage.finishButton.click()
        analysisPage.markReviewButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('shows the review comment on overview page', function() {
        loginPage.selectSecondUser()
        variantSelectionPage.expandReviewSection()
        expect(variantSelectionPage.getReviewComment()).toEqual('REVIEW_COMMENT_ROUND1')
    })

    it('keeps the classification from the previous round', function() {
        loginPage.selectSecondUser()
        variantSelectionPage.expandReviewSection()
        variantSelectionPage.selectTopReview()
        analysisPage.startButton.click()
        checkAlleleClassification(interpretation_expected_values)
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })
})
