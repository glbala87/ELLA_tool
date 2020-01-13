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
let failFast = require('jasmine-fail-fast')

let loginPage = new LoginPage()
let addExcludedAllelesModal = new AddExcludedAllelesModal()
let sampleSelectionPage = new SampleSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSidebar = new AlleleSidebar()
let alleleSectionBox = new AlleleSectionBox()
let workLog = new WorkLog()
let customAnnotationModal = new CustomAnnotationModal()
let referenceEvalModal = new ReferenceEvalModal()

jasmine.getEnv().addReporter(failFast.init())

const BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION = 'RE-EVALUATE'
const SAMPLE_ONE = 'brca_e2e_test01.HBOCUTV_v01'
const SAMPLE_TWO = 'brca_e2e_test02.HBOCUTV_v01'
const TITLE_INTERPRETATION = ' • INTERPRETATION'
const TITLE_REVIEW = ' • REVIEW'

// let timeOutForThisSpec = 3 * 60 * 1000;
// let originalTimeout = jasmine.DEFAULT_TIMEOUT_INTERVAL;
// jasmine.DEFAULT_TIMEOUT_INTERVAL = timeOutForThisSpec;

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
            } } } }' WHERE username IN ('testuser1', 'testuser2')
    `)
    expect(result).toEqual('UPDATE 2\n')
}

describe('Sample workflow', function() {
    console.log(
        'Starting test suite ' +
            "'Sample workflow' with a timeout of " +
            jasmine.DEFAULT_TIMEOUT_INTERVAL
    )

    beforeAll(() => {
        browser.resetDb()
    })

    it('allows and disallows finalize without classifying all variants if configured', function() {
        // Modify user config to allow finalization with classifying all variants

        loginPage.open()
        loginPage.loginAs('testuser1')
        browser.execute(`localStorage.clear()`) // Needs a proper URL, hence after login
        sampleSelectionPage.selectTopPending()

        expect(analysisPage.title).toBe(SAMPLE_ONE + TITLE_INTERPRETATION)
        analysisPage.startButton.click()

        setFinalizationRequirements(true, true, true, ['Interpretation'])
        browser.refresh()
        expect(analysisPage.getFinalizePossible()).toBe(true)
    })

    // Store entered data for interpretation round 1 {c.1234A>C: ...}
    // Will be checked against in round two
    let expected_analysis_1_round_1 = {}
    let expected_analysis_2_round_1 = {}

    it('allows interpretation, classification and reference evaluation to be set to review', function() {
        // For rest of the test, make sure all must be classified, except technical and not relevant
        setFinalizationRequirements(true, true, false)
        browser.refresh()
        expect(analysisPage.getFinalizePossible()).toBe(false)

        // Add excluded allele
        let number_of_variants_before_filter_change = alleleSidebar.getUnclassifiedAlleles().length
        expect(number_of_variants_before_filter_change).toBe(
            5,
            `Wrong number of variants of sample ${SAMPLE_ONE}. Please check the filtering rules or the annotation data in the vcf`
        )
        analysisPage.addExcludedButton.click()
        addExcludedAllelesModal.includeAllele(1)
        addExcludedAllelesModal.closeBtn.click()
        expect(alleleSidebar.getUnclassifiedAlleles().length).toEqual(
            number_of_variants_before_filter_change + 1
        )

        // Classify first three alleles with visual and quick classification
        analysisPage.classificationTypeVisualButton.scrollIntoView({ block: 'center' })
        analysisPage.classificationTypeVisualButton.click()
        alleleSidebar.quickSetTechnical('c.1233dupA')
        // Allele is selected automatically when setting technical
        let selected_allele = alleleSidebar.getSelectedAllele()
        expect(alleleSidebar.isAlleleInTechnical(selected_allele)).toBe(true)
        alleleSidebar.setTechnicalComment('c.1233dupA', 'TECHNICAL_ROUND_1')
        expected_analysis_1_round_1[selected_allele] = {
            technical: true,
            analysisComment: 'TECHNICAL_ROUND_1'
        }

        analysisPage.classificationTypeQuickButton.scrollIntoView({ block: 'center' })
        analysisPage.classificationTypeQuickButton.click()
        alleleSidebar.quickSetNotRelevant('c.925dupT')
        selected_allele = alleleSidebar.getSelectedAllele()
        expect(alleleSidebar.isAlleleInNotRelevant(selected_allele)).toBe(true)
        alleleSidebar.setNotRelevantComment('c.925dupT', 'NOTRELEVANT_ROUND_1')
        expected_analysis_1_round_1[selected_allele] = {
            notRelevant: true,
            analysisComment: 'NOTRELEVANT_ROUND_1'
        }

        alleleSidebar.quickClassU('c.1788T>C')
        selected_allele = alleleSidebar.getSelectedAllele()
        expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true)
        alleleSidebar.setEvaluationComment('c.1788T>C', 'EVALUATION_ROUND_1')
        expected_analysis_1_round_1[selected_allele] = {
            classification: 'U',
            evaluation: 'EVALUATION_ROUND_1'
        }

        // Classify rest using 'Full' classification view
        analysisPage.classificationTypeFullButton.scrollIntoView({ block: 'center' })
        analysisPage.classificationTypeFullButton.click()

        const exomesElement = alleleSectionBox.gnomADExomesElement
        expect(exomesElement).toBeDefined('Missing gnomeAD exomes box on the page')
        const genomesElement = alleleSectionBox.gnomADGenomesElement
        expect(genomesElement).toBeDefined('Missing gnomeAD genomes box on the page')

        // For the rest we perform more extensive classifications
        // Next allele is automatically selected by application
        for (let idx = 2; idx < 5; idx++) {
            // Move to next unclassified
            alleleSidebar.selectFirstUnclassified()
            selected_allele = alleleSidebar.getSelectedAllele()
            console.log(`Classifying variant ${selected_allele} in loop with idx=${idx}`)

            // Add attachment
            expect(alleleSectionBox.getNumberOfAttachments()).toEqual(0)
            analysisPage.addAttachment()
            expect(alleleSectionBox.getNumberOfAttachments()).toEqual(1)

            // Evaluate one reference
            let referenceTitle = alleleSectionBox.evaluateReference(1)
            console.log(`Evaluating reference ${referenceTitle}`)
            referenceEvalModal.setRelevance(1)
            referenceEvalModal.setComment('REFERENCE_EVAL_ROUND1')

            referenceEvalModal.saveBtn.click()
            referenceEvalModal.waitForClose()

            expect(alleleSectionBox.getReferenceComment(1)).toEqual('REFERENCE_EVAL_ROUND1')

            // Add external annotation
            console.log('Adding custom annotation')
            alleleSectionBox.addExternalBtn.click()
            customAnnotationModal.setExternalAnnotation(1, 'Likely pathogenic') // BRCA Exchange
            customAnnotationModal.saveBtn.click()
            customAnnotationModal.waitForClose()
            expect(alleleSectionBox.getExternalOtherAnnotation()).toEqual('BRCA Exchange:')
            expect(alleleSectionBox.getExternalOtherValue()).toEqual('likely_pathogenic')

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

            alleleSidebar.markClassifiedReview(selected_allele)
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true)

            // Check that we cannot finalize, as we're only in "Interpretation" workflow status
            expect(alleleSectionBox.finalizeBtn.isEnabled()).toBe(false)

            expected_analysis_1_round_1[selected_allele] = {
                reviewed: true,
                references: {
                    '1': {
                        relevance: 'Yes',
                        comment: 'REFERENCE_EVAL_ROUND1'
                    }
                },
                customAnnotation: {
                    external: {
                        'BRCA_Exchange-BRCA2': 'likely_pathogenic'
                    },
                    prediction: {
                        domain: 'critical_domain'
                    }
                },
                evaluation: 'EVALUATION_ROUND1',
                frequency: 'FREQUENCY_ROUND1',
                prediction: 'PREDICTION_ROUND1',
                external: 'EXTERNAL_ROUND1',
                report: 'REPORT_ROUND1 &~øæå',
                classification: (idx + 1).toString(),
                acmg: {
                    // Codes are sorted by pathogenicity/strength
                    '1': {
                        code: 'PS1 VERY STRONG',
                        comment: 'PS1_ACMG_ROUND_1'
                    },
                    '2': {
                        code: 'PS2 SUPPORTIVE',
                        comment: 'PS2_ACMG_ROUND_1'
                    },
                    '3': {
                        code: 'BP2',
                        comment: 'BP2_ACMG_ROUND_1'
                    }
                },
                num_attachments: 1
            }
        }

        // Make sure that we still cannot finalize,
        // even though all variants have a class (they're not finalized)
        expect(analysisPage.getFinalizePossible()).toBe(false)

        console.log('Changing to the report page')
        analysisPage.selectSectionReport()

        console.log('Setting a review comment and add a message')
        workLog.open()
        workLog.reviewCommentElement.setValue('REVIEW_COMMENT_ROUND1')
        workLog.reviewCommentUpdateBtn.click()
        workLog.addMessage('MESSAGE_ROUND_1')
        workLog.close()

        expect(alleleSidebar.getClassifiedAlleles().length).toEqual(
            4,
            `Wrong number of variants of sample ${SAMPLE_ONE} before finish`
        )

        console.log('Setting to review')
        analysisPage.finishButton.click()
        analysisPage.markReviewButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('shows the review comment on overview page', function() {
        loginPage.open()
        loginPage.loginAs('testuser2')
        sampleSelectionPage.expandReviewSection()
        expect(sampleSelectionPage.getReviewComment()).toEqual('REVIEW_COMMENT_ROUND1')
    })

    it('keeps the classification from the previous round', function() {
        loginPage.open()
        loginPage.loginAs('testuser2')
        sampleSelectionPage.expandReviewSection()
        sampleSelectionPage.selectTopReview()
        expect(analysisPage.title).toBe(SAMPLE_ONE + TITLE_REVIEW)
        analysisPage.startButton.click()
        checkAlleleClassification(expected_analysis_1_round_1)

        workLog.open()
        expect(workLog.getLastMessage()).toBe('MESSAGE_ROUND_1')
        workLog.close()

        // Finalize all classified variants (we're now in "Review" workflow status)
        const numberOfClassified = alleleSidebar.countOfClassified()
        for (let idx = 1; idx < numberOfClassified; idx++) {
            alleleSidebar.selectClassifiedAlleleByIdx(idx)
            alleleSectionBox.finalize()
        }

        expect(alleleSidebar.countOfUnclassified()).toBe(0)
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('reuses classified variants from a different sample', function() {
        loginPage.open()
        // Allow finalization directly from Interpretation
        setFinalizationRequirements(true, true, false, ['Interpretation'])
        browser.refresh()
        loginPage.open()
        loginPage.loginAs('testuser1')
        sampleSelectionPage.selectTopPending()

        expect(analysisPage.title).toBe(SAMPLE_TWO + TITLE_INTERPRETATION)

        analysisPage.startButton.click()

        // First check alleles overlapping with prev sample
        // that classifications were kept
        let overlapping_alleles = ['c.581G>A', 'c.475+3A>G', 'c.289G>T']
        let overlapping_classes = ['5', '4', '3']
        analysisPage.selectSectionClassification()

        let prev_classified = alleleSidebar.getClassifiedAlleles()
        expect(prev_classified).toEqual(overlapping_alleles)

        // Quickly classify two unclassified ones
        alleleSidebar.selectFirstUnclassified()
        alleleSectionBox.classSelection.selectByVisibleText('Class 1')
        alleleSectionBox.finalize()
        alleleSidebar.selectFirstUnclassified()
        alleleSectionBox.classSelection.selectByVisibleText(`Class 1`)
        alleleSectionBox.finalize()

        // Check that the others are reused by default
        for (let idx = 0; idx < overlapping_alleles.length; idx++) {
            alleleSidebar.selectClassifiedAllele(overlapping_alleles[idx])
            expect(alleleSidebar.getSelectedAlleleClassification().current).toEqual(
                overlapping_classes[idx]
            )
            expect(alleleSectionBox.reevaluateBtn.isDisplayed()).toBe(true)
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
        }

        // Reviewed is reset since this is a new sample
        allele_data['c.581G>A'].reviewed = false
        allele_data['c.475+3A>G'].reviewed = false
        allele_data['c.289G>T'].reviewed = false

        checkAlleleClassification(allele_data)

        // start: make changes to classification on a variant that overlaps with the third sample:
        alleleSidebar.selectClassifiedAllele('c.581G>A')
        alleleSectionBox.reevaluateBtn.click()
        alleleSectionBox.reEvaluateReference(1)
        referenceEvalModal.setRelevance(2)
        referenceEvalModal.setComment('REFERENCE_EVAL_UPDATED')
        referenceEvalModal.saveBtn.scrollIntoView({ block: 'center' })
        referenceEvalModal.saveBtn.click()
        referenceEvalModal.waitForClose()

        alleleSectionBox.setClassificationComment('EVALUATION_UPDATED')
        alleleSectionBox.setFrequencyComment('FREQUENCY_UPDATED')
        alleleSectionBox.setPredictionComment('PREDICTION_UPDATED')
        alleleSectionBox.setExternalComment('EXTERNAL_UPDATED')
        alleleSectionBox.setReportComment('REPORT_UPDATED')
        alleleSectionBox.classSelection.selectByVisibleText('Class 5')
        analysisPage.addAttachment()
        expect(alleleSectionBox.getNumberOfAttachments()).toEqual(2)
        alleleSectionBox.finalize()
        // :end

        expected_analysis_2_round_1['c.581G>A'] = expected_analysis_1_round_1['c.581G>A']
        expected_analysis_2_round_1['c.581G>A'].reviewed = false

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
            num_attachments: 2
        })

        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('reuses the latest variant classification done in another sample', function() {
        loginPage.open()
        loginPage.loginAs('testuser1')
        sampleSelectionPage.selectFindings(1)
        checkAlleleClassification(expected_analysis_2_round_1)
    })
})
