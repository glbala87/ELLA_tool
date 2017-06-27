require('core-js/fn/object/entries');

/**
 * Performs interpretations for three samples and evaluate some references.
 * - Sample 1: interpret one round, set to review.
 * - Sample 1: check if interpretations from previous round is stored. Finalize the sample.
 * - Sample 2: check if variants common with sample 1 are already classified.
 *             change a variant that also exists in sample 3
 * - Sample 3: confirm that the changed classification in 2nd sample is carried
 *             over correctly, and that it's using the latest classification rather
 *             than the first one made as part of 1st sample.
 */

let LoginPage = require('../pageobjects/loginPage')
let AddExcludedAllelesModal = require('../pageobjects/addExcludedModal')
let SampleSelectionPage = require('../pageobjects/overview_samples')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSidebar = require('../pageobjects/alleleSidebar')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let CustomAnnotationModal = require('../pageobjects/customAnnotationModal')
let ReferenceEvalModal = require('../pageobjects/referenceEvalModal')
let checkAlleleClassification = require('../helpers/checkAlleleClassification')
let failFast = require('jasmine-fail-fast');

let loginPage = new LoginPage()
let addExcludedAllelesModal = new AddExcludedAllelesModal()
let sampleSelectionPage = new SampleSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSidebar = new AlleleSidebar()
let alleleSectionBox = new AlleleSectionBox()
let customAnnotationModal = new CustomAnnotationModal()
let referenceEvalModal = new ReferenceEvalModal()

jasmine.getEnv().addReporter(failFast.init());

const BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION = 'REEVALUATE';
const SAMPLE_ONE = 'brca_e2e_test01.HBOCUTV_v01';

describe('Sample workflow', function () {

    beforeAll(() => {
        browser.resetDb();
    });

    // Store entered data for interpretation round 1 {c.1234A>C: ...}
    // Will be checked against in round two
    let expected_analysis_1_round_1 = {};
    let expected_analysis_2_round_1 = {};

    it('allows interpretation, classification and reference evaluation to be set to review', function () {
        loginPage.selectFirstUser();
        sampleSelectionPage.selectTopPending();

        analysisPage.startButton.click();

        // Add excluded allele
        let number_of_variants_before_filter_change = alleleSidebar.getUnclassifiedAlleles().length;
        expect(number_of_variants_before_filter_change).toEqual(5, `Wrong number of variants of sample ${SAMPLE_ONE}`);
        analysisPage.addExcludedButton.click();
        addExcludedAllelesModal.includeAlleleBtn.click();
        addExcludedAllelesModal.closeBtn.click();
        expect(alleleSidebar.getUnclassifiedAlleles().length).toEqual(number_of_variants_before_filter_change + 1);

        // Classify first three alleles quickly
        alleleSidebar.selectFirstUnclassified();
        let selected_allele = alleleSidebar.getSelectedAllele();
        alleleSectionBox.markAsClass1();
        expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true);
        expected_analysis_1_round_1[selected_allele] = {classification: '1'};

        alleleSidebar.selectUnclassifiedAllele('c.925dupT');
        selected_allele = alleleSidebar.getSelectedAllele();
        alleleSectionBox.markAsClass2();
        expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true);
        expected_analysis_1_round_1[selected_allele] = {classification: '2'};

        alleleSidebar.selectUnclassifiedAllele('c.1788T>C');
        selected_allele = alleleSidebar.getSelectedAllele();
        alleleSectionBox.markAsTechnical();
        expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true);
        expected_analysis_1_round_1[selected_allele] = {classification: 'T'};

        // For the rest we perform more extensive classifications
        // Next allele is automatically selected by application
        for (let idx = 2; idx < 5; idx++) {

            // Move to next unclassified
            alleleSidebar.selectFirstUnclassified();
            selected_allele = alleleSidebar.getSelectedAllele();
            console.log(`Classifying variant ${selected_allele} in loop with idx=${idx}`);

            // Add attachment
            expect(alleleSectionBox.getNumberOfAttachments()).toEqual(0);
            alleleSectionBox.addAttachment()
            expect(alleleSectionBox.getNumberOfAttachments()).toEqual(1);

            // Evaluate one reference
            let referenceTitle = alleleSectionBox.evaluateReference(1);
            console.log(`Evaluating reference ${referenceTitle}`);
            referenceEvalModal.setRelevance(1);
            referenceEvalModal.setComment('REFERENCE_EVAL_ROUND1');

            referenceEvalModal.saveBtn.scroll();
            referenceEvalModal.saveBtn.click();

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
            customAnnotationModal.annotationSelect.selectByVisibleText('Ortholog conservation');
            customAnnotationModal.valueSelect.selectByVisibleText('Conserved');
            customAnnotationModal.addBtn.click();
            customAnnotationModal.saveBtn.click();
            expect(alleleSectionBox.getPredictionOtherAnnotation()).toEqual('Ortholog conservation:');
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
            alleleSectionBox.addAcmgCode('pathogenic', 'PS2','ACMG_ROUND_1', -2); // Adjust down to PPxPS2
            alleleSectionBox.addAcmgCode('pathogenic', 'PS2','ACMG_ROUND_1', 1); // Adjust up to PVSxPS1
            alleleSectionBox.classSelection.selectByVisibleText(`Class ${idx+1}`);

            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true);

            expected_analysis_1_round_1[selected_allele] = {
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
                classification: (idx+1).toString(),
                acmg: [
                    {
                        code: 'BP2',
                        category: 'benign',
                        comment: 'ACMG_ROUND_1'
                    },
                    {
                        code: 'PPxPS2',
                        category: 'pathogenic',
                        comment: 'ACMG_ROUND_1'
                    },
                    {
                        code: 'PVSxPS1',
                        category: 'pathogenic',
                        comment: 'ACMG_ROUND_1'
                    },
                ],
                num_attachments: 1,
            }
        }

        analysisPage.selectSectionReport();
        alleleSectionBox.reviewCommentElement.setValue('REVIEW_COMMENT_ROUND1');
        expect(alleleSidebar.getClassifiedAlleles().length)
            .toEqual(6, `Wrong number of variants of sample ${SAMPLE_ONE} before finish`);
        analysisPage.finishButton.click();
        analysisPage.markReviewButton.click();
    });

    it('shows the review comment on overview page', function () {
        loginPage.selectSecondUser();
        sampleSelectionPage.expandReviewSection();
        expect(sampleSelectionPage.getReviewComment()).toEqual('REVIEW_COMMENT_ROUND1');
    });

    it('keeps the classification from the previous round', function () {

        loginPage.selectSecondUser();
        sampleSelectionPage.expandReviewSection();
        sampleSelectionPage.selectTopReview();
        analysisPage.startButton.click();
        checkAlleleClassification(expected_analysis_1_round_1);
        analysisPage.finishButton.click();
        analysisPage.finalizeButton.click();
    });

    it('reuses classified variants from a different sample', function() {

        loginPage.selectFirstUser();
        sampleSelectionPage.selectTopPending();
        analysisPage.startButton.click();

        // First check alleles overlapping with prev sample
        // that classifications were kept
        let overlapping_alleles = ['c.581G>A', 'c.475+3A>G', 'c.289G>T'];
        let overlapping_classes = ['5', '4', '3'];
        analysisPage.selectSectionClassification();

        let prev_classified = alleleSidebar.getClassifiedAlleles();
        expect(prev_classified).toEqual(overlapping_alleles);

        // Quickly classify two unclassified ones
        alleleSidebar.selectFirstUnclassified();
        alleleSectionBox.classSelection.selectByVisibleText('Class 1');
        alleleSidebar.selectFirstUnclassified();
        alleleSectionBox.classSelection.selectByVisibleText(`Class 1`);

        // Check that the others are accepted by default
        for (let idx = 0; idx < overlapping_alleles.length; idx++) {
            alleleSidebar.selectClassifiedAllele(overlapping_alleles[idx]);
            expect(alleleSidebar.getSelectedAlleleClassification()).toEqual(overlapping_classes[idx]);
            expect(alleleSectionBox.classificationAcceptedBtn.getText()).toEqual(BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION);
        }

        // Finally check the data of all our selections.
        let allele_data = {
            'c.581G>A': expected_analysis_1_round_1['c.581G>A'],
            'c.475+3A>G': expected_analysis_1_round_1['c.475+3A>G'],
            'c.289G>T': expected_analysis_1_round_1['c.289G>T'],
            'c.10G>T': {
                classification: '1'
            },
            'c.198A>G': {
                classification: '1'
            }
        };
        checkAlleleClassification(allele_data);

        // start: make changes to classification on a variant that overlaps with the third sample:
        alleleSidebar.selectClassifiedAllele('c.581G>A');
        alleleSectionBox.classificationAcceptedBtn.click();
        let referenceTitle = alleleSectionBox.evaluateReference(1);
        referenceEvalModal.setRelevance(2);
        referenceEvalModal.setComment('REFERENCE_EVAL_UPDATED');
        referenceEvalModal.saveBtn.scroll();
        referenceEvalModal.saveBtn.click();
        alleleSectionBox.setClassificationComment('EVALUATION_UPDATED');
        analysisPage.saveButton.scroll();
        analysisPage.saveButton.click();
        alleleSectionBox.setFrequencyComment('FREQUENCY_UPDATED');
        analysisPage.saveButton.scroll();
        analysisPage.saveButton.click();
        alleleSectionBox.setPredictionComment('PREDICTION_UPDATED');
        analysisPage.saveButton.scroll();
        analysisPage.saveButton.click();
        alleleSectionBox.setExternalComment('EXTERNAL_UPDATED');
        analysisPage.saveButton.scroll();
        analysisPage.saveButton.click();
        alleleSectionBox.setReportComment('REPORT_UPDATED');
        alleleSectionBox.classSelection.selectByVisibleText('Class 5');
        alleleSectionBox.addAttachment()
        expect(alleleSectionBox.getNumberOfAttachments()).toEqual(2);
        // :end

        expected_analysis_2_round_1['c.581G>A'] = expected_analysis_1_round_1['c.581G>A'];
        Object.assign(expected_analysis_2_round_1['c.581G>A'], {
            evaluation: 'EVALUATION_UPDATED',
            frequency: 'FREQUENCY_UPDATED',
            prediction: 'PREDICTION_UPDATED',
            external: 'EXTERNAL_UPDATED',
            report: 'REPORT_UPDATED',
            classification: '5',
            references: {
                '1': {
                    comment: 'REFERENCE_EVAL_UPDATED',
                    relevance: 'Indirectly'
                }
            },
            num_attachments: 2,
        });

        analysisPage.finishButton.click();
        analysisPage.finalizeButton.click();

    });

    it('reuses the latest variant classification done in another sample', function() {

        loginPage.selectFirstUser();
        sampleSelectionPage.selectFindings(1);
        checkAlleleClassification(expected_analysis_2_round_1);
    });

});
