require('core-js/fn/object/entries')

let LoginPage = require('../pageobjects/loginPage')
let SampleSelectionPage = require('../pageobjects/overview_samples')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSidebar = require('../pageobjects/alleleSidebar')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let WorkLog = require('../pageobjects/workLog')
let CustomAnnotationModal = require('../pageobjects/customAnnotationModal')
let ReferenceEvalModal = require('../pageobjects/referenceEvalModal')
let checkAlleleClassification = require('../helpers/checkAlleleClassification')

let loginPage = new LoginPage()
let sampleSelectionPage = new SampleSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSidebar = new AlleleSidebar()
let alleleSectionBox = new AlleleSectionBox()
let workLog = new WorkLog()
let customAnnotationModal = new CustomAnnotationModal()
let referenceEvalModal = new ReferenceEvalModal()

const SAMPLE_ONE = 'HG002-Trio.Mendeliome_v1.0.0'
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
        expect(alleleSidebar.getCurrentFilterConfig()).toBe('TrioDefault')
        alleleSidebar.selectFilterConfig('SingleDefault')
        analysisPage.saveButton.click()

        let selectedAllele = alleleSidebar.getSelectedAllele()
        expect(selectedAllele).toBe('c.4958_4975dup')

        setFinalizationRequirements(true, true, true, ['Interpretation'])
        browser.refresh()
        expect(analysisPage.getFinalizePossible()).toBe(true)
        expect(alleleSidebar.getCurrentFilterConfig()).toBe('SingleDefault')
    })

    // Store entered data for interpretation round 1 {c.1234A>C: ...}
    // Will be checked against in round two
    let expected_analysis_1_round_1 = {}

    it('allows interpretation, classification and reference evaluation to be set to review', function() {
        setFinalizationRequirements(true, true, false)
        browser.refresh()
        expect(analysisPage.getFinalizePossible()).toBe(false)

        expect(analysisPage.title).toBe(SAMPLE_ONE + TITLE_INTERPRETATION)

        const cnvSelector = analysisPage.cnvSelector
        cnvSelector.waitForExist()
        cnvSelector.click()

        unclassifiedCnvs = alleleSidebar.countOfUnclassified()
        expect(unclassifiedCnvs).toBe(7)

        analysisPage.classificationTypeVisualButton.scrollIntoView({ block: 'center' })
        analysisPage.classificationTypeVisualButton.click()
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

        // Classify some events using 'Full' classification view
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

            // Evaluate one reference
            /** TODO: update database so there are articles for some the test data 
            let referenceTitle = alleleSectionBox.evaluateReference(1)
            console.log(`Evaluating reference ${referenceTitle}`)
            referenceEvalModal.setRelevance(1)
            referenceEvalModal.setComment('REFERENCE_EVAL_ROUND1')

            referenceEvalModal.saveBtn.click()
            referenceEvalModal.waitForClose()

            expect(alleleSectionBox.getReferenceComment(1)).toEqual('REFERENCE_EVAL_ROUND1')
            */

            // // Add external annotation
            console.log('Adding custom annotation')
            alleleSectionBox.addExternalBtn.click()
            customAnnotationModal.setExternalAnnotationText('structural variant info')
            customAnnotationModal.saveBtn.click()
            customAnnotationModal.waitForClose()
            expect(alleleSectionBox.getExternalOtherValue()).toEqual('structural variant info')

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
            alleleSectionBox.setClassificationComment('EVALUATION_ROUND_1')
            analysisPage.saveButton.click()
            alleleSectionBox.setFrequencyComment('FREQUENCY_ROUND_1')
            analysisPage.saveButton.click()
            alleleSectionBox.setPredictionComment('PREDICTION_ROUND_1')
            analysisPage.saveButton.click()
            alleleSectionBox.setExternalComment('EXTERNAL_ROUND_1')
            analysisPage.saveButton.click()

            alleleSectionBox.setReportComment('REPORT_ROUND_1 &~øæå')

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

            alleleSidebar.markClassifiedReview(selected_allele)
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true)

            // Check that we cannot finalize, as we're only in "Interpretation" workflow status
            expect(alleleSectionBox.finalizeBtn.isEnabled()).toBe(false)
            expected_analysis_1_round_1[selected_allele] = {
                reviewed: true,
                customAnnotation: {
                    external: {
                        Other: 'structural variant info'
                    },
                    prediction: {
                        domain: 'critical_domain'
                    }
                },
                evaluation: 'EVALUATION_ROUND_1',
                frequency: 'FREQUENCY_ROUND_1',
                prediction: 'PREDICTION_ROUND_1',
                external: 'EXTERNAL_ROUND_1',
                report: 'REPORT_ROUND_1 &~øæå',
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
        workLog.reviewCommentElement.setValue('REVIEW_COMMENT_ROUND_1')
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
        loginPage.loginAs('testuser4')
        sampleSelectionPage.expandReviewSection()
        expect(sampleSelectionPage.getReviewComment()).toEqual('REVIEW_COMMENT_ROUND_1')
    })

    it('keeps the classification from the previous round', function() {
        loginPage.open()
        loginPage.loginAs('testuser4')
        sampleSelectionPage.expandReviewSection()
        sampleSelectionPage.selectTopReview()
        expect(analysisPage.title).toBe(SAMPLE_ONE + TITLE_REVIEW)
        analysisPage.startButton.click()

        const cnvSelector = analysisPage.cnvSelector
        cnvSelector.waitForExist()
        cnvSelector.click()

        checkAlleleClassification(expected_analysis_1_round_1)

        workLog.open()
        expect(workLog.getLastMessage()).toBe('MESSAGE_ROUND_1')
        workLog.close()

        // Finalize all classified variants (we're now in "Review" workflow status)
        const numberOfClassified = alleleSidebar.countOfClassified()
        for (let idx = 1; idx < numberOfClassified + 1; idx++) {
            alleleSidebar.selectClassifiedAlleleByIdx(idx)
            alleleSectionBox.finalize()
        }

        expect(alleleSidebar.countOfUnclassified()).toBe(1)
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })
})
