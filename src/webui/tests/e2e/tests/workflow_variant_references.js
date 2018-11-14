require('core-js/fn/object/entries')

/**
 * Add a reference by pasting XML, (variant workflow)
 */

let LoginPage = require('../pageobjects/loginPage')
let VariantSelectionPage = require('../pageobjects/overview_variants')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let CustomAnnotationModal = require('../pageobjects/customAnnotationModal')
let failFast = require('jasmine-fail-fast')

let loginPage = new LoginPage()
let variantSelectionPage = new VariantSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSectionBox = new AlleleSectionBox()
let customAnnotationModal = new CustomAnnotationModal()

jasmine.getEnv().addReporter(failFast.init())

const OUR_VARIANT = 'c.581G>A'

describe(`Adding reference in variant workflow (using ${OUR_VARIANT}`, function() {
    beforeAll(() => {
        browser.resetDb()
    })

    // Update expectations as we do interpretations in the UI
    let interpretation_expected_values = {}

    it('allows interpretation, classification and reference evaluation to be set to review', function() {
        loginPage.selectFirstUser()
        variantSelectionPage.selectPending(7)
        analysisPage.startButton.click()
        alleleSectionBox.classifyAsU()

        expect(alleleSectionBox.getReferences().value.length).toEqual(4)

        // add a reference
        console.log(`adding references`)
        alleleSectionBox.addReferencesBtn.click()
        let referenceList = customAnnotationModal.referenceList()
        const beforeCount = referenceList ? referenceList.value.length : 0
        customAnnotationModal.pubMedBtn.click()
        customAnnotationModal.setText(customAnnotationModal.xmlInputEditor, XML_PUBMED)
        customAnnotationModal.addReferenceBtn.click()
        const afterCount = customAnnotationModal.referenceList().value.length
        expect(afterCount).toEqual(beforeCount + 1)
        customAnnotationModal.saveBtn.click()
        customAnnotationModal.waitForClose()

        expect(alleleSectionBox.getReferences().value.length).toEqual(5)

        alleleSectionBox.classSelection.selectByVisibleText('Class 1')
        analysisPage.finishButton.click()
        analysisPage.markReviewButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('shows references added in review', function() {
        loginPage.selectSecondUser()
        variantSelectionPage.expandReviewSection()
        variantSelectionPage.selectTopReview()
        expect(alleleSectionBox.getReferences().value.length).toEqual(5)
        analysisPage.startButton.click()
        expect(alleleSectionBox.getReferences().value.length).toEqual(5)
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('shows references for completed interpretation ', function() {
        loginPage.selectSecondUser()
        variantSelectionPage.expandFinishedSection()
        variantSelectionPage.selectFinished(1)
        expect(alleleSectionBox.getReferences().value.length).toEqual(5)
    })
})

const XML_PUBMED = `
<PubmedArticle>
    <MedlineCitation Status="In-Data-Review" Owner="NLM">
        <PMID Version="1">28148507</PMID>
        <DateCreated>
            <Year>2017</Year>
            <Month>02</Month>
            <Day>02</Day>
        </DateCreated>
        <DateRevised>
            <Year>2017</Year>
            <Month>02</Month>
            <Day>02</Day>
        </DateRevised>
        <Article PubModel="Print">
            <Journal>
                <ISSN IssnType="Electronic">1938-3207</ISSN>
                <JournalIssue CitedMedium="Internet">
                    <Volume>105</Volume>
                    <Issue>2</Issue>
                    <PubDate>
                        <Year>2017</Year>
                        <Month>Feb</Month>
                    </PubDate>
                </JournalIssue>
                <Title>The American journal of clinical nutrition</Title>
                <ISOAbbreviation>Am. J. Clin. Nutr.</ISOAbbreviation>
            </Journal>
            <ArticleTitle>Erratum for Traber et al. α-Tocopherol disappearance rates from plasma depend on lipid concentrations: studies using deuterium-labeled collard greens in younger and older adults. Am J Clin Nutr 2015;101:752-9.</ArticleTitle>
            <Pagination>
                <MedlinePgn>543</MedlinePgn>
            </Pagination>
            <ELocationID EIdType="doi" ValidYN="Y">10.3945/ajcn.116.150219</ELocationID>
            <Language>eng</Language>
            <PublicationTypeList>
                <PublicationType UI="">Journal Article</PublicationType>
                <PublicationType UI="">Published Erratum</PublicationType>
            </PublicationTypeList>
        </Article>
        <MedlineJournalInfo>
            <Country>United States</Country>
            <MedlineTA>Am J Clin Nutr</MedlineTA>
            <NlmUniqueID>0376027</NlmUniqueID>
            <ISSNLinking>0002-9165</ISSNLinking>
        </MedlineJournalInfo>
        <CommentsCorrectionsList>
            <CommentsCorrections RefType="ErratumFor">
                <RefSource>Am J Clin Nutr. 2015 Apr;101(4):752-9</RefSource>
                <PMID Version="1">25739929</PMID>
            </CommentsCorrections>
        </CommentsCorrectionsList>
    </MedlineCitation>
    <PubmedData>
        <History>
            <PubMedPubDate PubStatus="entrez">
                <Year>2017</Year>
                <Month>2</Month>
                <Day>3</Day>
                <Hour>6</Hour>
                <Minute>0</Minute>
            </PubMedPubDate>
            <PubMedPubDate PubStatus="pubmed">
                <Year>2017</Year>
                <Month>2</Month>
                <Day>6</Day>
                <Hour>6</Hour>
                <Minute>0</Minute>
            </PubMedPubDate>
            <PubMedPubDate PubStatus="medline">
                <Year>2017</Year>
                <Month>2</Month>
                <Day>6</Day>
                <Hour>6</Hour>
                <Minute>0</Minute>
            </PubMedPubDate>
        </History>
        <PublicationStatus>ppublish</PublicationStatus>
        <ArticleIdList>
            <ArticleId IdType="pubmed">28148507</ArticleId>
            <ArticleId IdType="pii">105/2/543</ArticleId>
            <ArticleId IdType="doi">10.3945/ajcn.116.150219</ArticleId>
        </ArticleIdList>
    </PubmedData>
</PubmedArticle>
`
