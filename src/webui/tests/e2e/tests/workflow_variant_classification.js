require('core-js/fn/object/entries');

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
let failFast = require('jasmine-fail-fast');

let loginPage = new LoginPage()
let variantSelectionPage = new VariantSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSectionBox = new AlleleSectionBox()
let customAnnotationModal = new CustomAnnotationModal()
let referenceEvalModal = new ReferenceEvalModal()

jasmine.getEnv().addReporter(failFast.init());

const OUR_VARIANT =  'c.581G>A';

describe(`Variant workflow (using ${OUR_VARIANT}`, function () {

    beforeAll(() => {
        browser.resetDb();
    });

    // Update expectations as we do interpretations in the UI
    let interpretation_expected_values = {};

    it('allows interpretation, classification and reference evaluation to be set to review', function () {
        loginPage.selectFirstUser();
        variantSelectionPage.selectPending(5);
        analysisPage.startButton.click();

        alleleSectionBox.markAsTechnical();

        // Evaluate one reference
        let referenceTitle = alleleSectionBox.evaluateReference(1);
        console.log(`Evaluating reference ${referenceTitle}`);
        referenceEvalModal.setRelevance(1);
        referenceEvalModal.setComment('REFERENCE_EVAL_ROUND1');

        referenceEvalModal.saveBtn.scroll();
        referenceEvalModal.saveBtn.click();

        expect(alleleSectionBox.getReferenceRelevance(1)).toEqual('Yes');
        expect(alleleSectionBox.getReferenceComment(1)).toEqual('REFERENCE_EVAL_ROUND1');

        // Add external annotation
        alleleSectionBox.addExternalBtn.scroll();
        alleleSectionBox.addExternalBtn.click();
        customAnnotationModal.annotationSelect.selectByVisibleText('LOVD');
        customAnnotationModal.valueSelect.selectByVisibleText('+/+');
        customAnnotationModal.addBtn.click();
        customAnnotationModal.saveBtn.click();
        expect(alleleSectionBox.getExternalOtherAnnotation()).toEqual('LOVD:');
        expect(alleleSectionBox.getExternalOtherValue()).toEqual('+/+');

        // Add prediction annotation
        alleleSectionBox.addPredictionBtn.scroll();
        alleleSectionBox.addPredictionBtn.click();
        customAnnotationModal.annotationSelect.selectByVisibleText('Conservation');
        customAnnotationModal.valueSelect.selectByVisibleText('conserved');
        customAnnotationModal.addBtn.click();
        customAnnotationModal.saveBtn.click();
        expect(alleleSectionBox.getPredictionOtherAnnotation()).toEqual('Conservation:');
        expect(alleleSectionBox.getPredictionOtherValue()).toEqual('conserved');

        // Set comments/classification
        alleleSectionBox.setClassificationComment('EVALUATION_ROUND1');
        analysisPage.saveButton.click();
        alleleSectionBox.setFrequencyComment('FREQUENCY_ROUND1');
        analysisPage.saveButton.scroll();
        analysisPage.saveButton.click();
        alleleSectionBox.setPredictionComment('PREDICTION_ROUND1');
        analysisPage.saveButton.scroll();
        analysisPage.saveButton.click();
        alleleSectionBox.setExternalComment('EXTERNAL_ROUND1');
        analysisPage.saveButton.scroll();
        analysisPage.saveButton.click();
        alleleSectionBox.setReportComment('REPORT_ROUND1');
        browser.click('body'); // a trick to unfocus the above report comment

        alleleSectionBox.classificationCommentElement.scroll();

        alleleSectionBox.addAcmgCode('benign', 'BP2','ACMG_ROUND_1');
        alleleSectionBox.addAcmgCode('pathogenic', 'PS2','ACMG_ROUND_1');
        alleleSectionBox.classSelection.selectByVisibleText('Class 1');

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
                        LOVD: '+/+'
                    },
                    prediction: {
                        Conservation: 'conserved'
                    }
                },
                evaluation: 'EVALUATION_ROUND1',
                frequency: 'FREQUENCY_ROUND1',
                prediction: 'PREDICTION_ROUND1',
                external: 'EXTERNAL_ROUND1',
                report: 'REPORT_ROUND1',
                classification: '1',
                acmg: [
                    {
                        code: 'BP2',
                        category: 'benign',
                        comment: 'ACMG_ROUND_1'
                    },
                    {
                        code: 'PS2',
                        category: 'pathogenic',
                        comment: 'ACMG_ROUND_1'
                    },
                ]
            }
        };

        alleleSectionBox.reviewCommentElement.setValue('REVIEW_COMMENT_ROUND1');
        analysisPage.finishButton.click();
        analysisPage.markReviewButton.click();
    });

    it('shows the review comment on overview page', function () {
        loginPage.selectSecondUser();
        variantSelectionPage.expandReviewSection();
        expect(variantSelectionPage.getReviewComment()).toEqual('REVIEW_COMMENT_ROUND1');
    });

    it('keeps the classification from the previous round', function () {
        loginPage.selectSecondUser();
        variantSelectionPage.expandReviewSection();
        variantSelectionPage.selectTopReview();
        analysisPage.startButton.click();
        checkAlleleClassification(interpretation_expected_values);
        analysisPage.finishButton.click();
        analysisPage.finalizeButton.click();
    });


    it('shows previous rounds when opening a finalized variant', function () {
        loginPage.selectSecondUser();
        variantSelectionPage.expandFinishedSection();
        variantSelectionPage.selectFinished(1);
        expect(analysisPage.roundCount).toBe(2);

    });


});