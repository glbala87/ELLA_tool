require('core-js/fn/object/entries')

/**
 * Add a reference by pasting XML, (variant workflow)
 */

let LoginPage = require('../pageobjects/loginPage')
let VariantSelectionPage = require('../pageobjects/overview_variants')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let CustomAnnotationModal = require('../pageobjects/customAnnotationModal')

let loginPage = new LoginPage()
let variantSelectionPage = new VariantSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSectionBox = new AlleleSectionBox()
let customAnnotationModal = new CustomAnnotationModal()

const OUR_VARIANT = 'c.581G>A'

describe(`Adding reference in variant workflow (using ${OUR_VARIANT}`, function() {
    beforeAll(() => {
        browser.resetDb()
    })

    // Update expectations as we do interpretations in the UI
    let interpretation_expected_values = {}

    it('allows interpretation, classification and reference evaluation to be set to review', function() {
        loginPage.open()
        loginPage.loginAs('testuser1')
        variantSelectionPage.selectPending(7)
        analysisPage.startButton.click()
        alleleSectionBox.classifyAsU()

        expect(alleleSectionBox.getReferences().length).toEqual(4)

        // add a reference using XML format
        console.log(`adding XML reference`)
        alleleSectionBox.addReferencesBtn.click()
        let referenceList = customAnnotationModal.referenceList()
        let beforeCount = referenceList.length
        customAnnotationModal.pubMedBtn.click()
        customAnnotationModal.rawInputEditor.setValue(XML_PUBMED)
        customAnnotationModal.addReferenceBtn.click()
        let afterCount = customAnnotationModal.referenceList().length
        expect(afterCount).toEqual(beforeCount + 1)
        customAnnotationModal.saveBtn.click()
        customAnnotationModal.waitForClose()

        expect(alleleSectionBox.getReferences().length).toEqual(5)

        // add a reference using RIS format
        console.log(`adding RIS reference`)
        alleleSectionBox.addReferencesBtn.click()
        referenceList = customAnnotationModal.referenceList()
        beforeCount = referenceList.length
        customAnnotationModal.pubMedBtn.click()
        customAnnotationModal.rawInputEditor.setValue(RIS_PUBMED)
        customAnnotationModal.addReferenceBtn.click()
        afterCount = customAnnotationModal.referenceList().length
        expect(afterCount).toEqual(beforeCount + 1)
        customAnnotationModal.saveBtn.click()
        customAnnotationModal.waitForClose()

        expect(alleleSectionBox.getReferences().length).toEqual(6)

        alleleSectionBox.classSelection.selectByVisibleText('Class 1')
        analysisPage.finishButton.click()
        analysisPage.markReviewButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('shows references added in review', function() {
        loginPage.open()
        loginPage.loginAs('testuser2')
        variantSelectionPage.expandReviewSection()
        variantSelectionPage.selectTopReview()
        expect(alleleSectionBox.getReferences().length).toEqual(6)
        analysisPage.startButton.click()
        expect(alleleSectionBox.getReferences().length).toEqual(6)
        alleleSectionBox.finalize()
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('shows references for completed interpretation ', function() {
        loginPage.open()
        loginPage.loginAs('testuser2')
        variantSelectionPage.expandFinishedSection()
        variantSelectionPage.selectFinished(1)
        expect(alleleSectionBox.getReferences().length).toEqual(6)
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

const RIS_PUBMED = `
PMID- 31448845
OWN - NLM
STAT- In-Data-Review
LR  - 20191224
IS  - 1098-1004 (Electronic)
IS  - 1059-7794 (Linking)
VI  - 41
IP  - 1
DP  - 2020 Jan
TI  - CRAT missense variants cause abnormal carnitine acetyltransferase function in an
      early-onset case of Leigh syndrome.
PG  - 110-114
LID - 10.1002/humu.23901 [doi]
AB  - Leigh syndrome, or subacute necrotizing encephalomyelopathy, is one of the most
      severe pediatric disorders of the mitochondrial energy metabolism. By performing
      whole-exome sequencing in a girl affected by Leigh syndrome and her parents, we
      identified two heterozygous missense variants (p.Tyr110Cys and p.Val569Met) in the
      carnitine acetyltransferase (CRAT) gene, encoding an enzyme involved in the control
      of mitochondrial short-chain acyl-CoA concentrations. Biochemical assays revealed
      carnitine acetyltransferase deficiency in the proband-derived fibroblasts.
      Functional analyses of recombinant-purified CRAT proteins demonstrated that both
      missense variants, located in the acyl-group binding site of the enzyme, severely
      impair its catalytic function toward acetyl-CoA, and the p.Val569Met variant also
      toward propionyl-CoA and octanoyl-CoA. Although a single recessive variant in CRAT
      has been recently associated with neurodegeneration with brain iron accumulation
      (NBIA), this study reports the first kinetic analysis of naturally occurring CRAT
      variants and demonstrates the genetic basis of carnitine acetyltransferase
      deficiency in a case of mitochondrial encephalopathy.
CI  - © 2019 Wiley Periodicals, Inc.
FAU - Laera, Luna
AU  - Laera L
AD  - Department of Biosciences, Biotechnology and Biopharmaceutics, University of Bari,
      Bari, Italy.
FAU - Punzi, Giuseppe
AU  - Punzi G
AD  - Department of Biosciences, Biotechnology and Biopharmaceutics, University of Bari,
      Bari, Italy.
FAU - Porcelli, Vito
AU  - Porcelli V
AD  - Department of Biosciences, Biotechnology and Biopharmaceutics, University of Bari,
      Bari, Italy.
FAU - Gambacorta, Nicola
AU  - Gambacorta N
AD  - Department of Biosciences, Biotechnology and Biopharmaceutics, University of Bari,
      Bari, Italy.
FAU - Trisolini, Lucia
AU  - Trisolini L
AD  - Department of Biosciences, Biotechnology and Biopharmaceutics, University of Bari,
      Bari, Italy.
FAU - Pierri, Ciro L
AU  - Pierri CL
AD  - Department of Biosciences, Biotechnology and Biopharmaceutics, University of Bari,
      Bari, Italy.
FAU - De Grassi, Anna
AU  - De Grassi A
AUID- ORCID: 0000-0001-7273-4263
AD  - Department of Biosciences, Biotechnology and Biopharmaceutics, University of Bari,
      Bari, Italy.
LA  - eng
GR  - MITOCON, Italian Association for the study and the cure of mitochondrial disorders/
GR  - MIUR, Italian Ministry of Education and Research/
PT  - Journal Article
DEP - 20190923
PL  - United States
TA  - Hum Mutat
JT  - Human mutation
JID - 9215429
SB  - IM
OTO - NOTNLM
OT  - CRAT
OT  - Leigh syndrome
OT  - carnitine acetyltransferase
OT  - mitochondrial encephalopathy
EDAT- 2019/08/27 06:00
MHDA- 2019/08/27 06:00
CRDT- 2019/08/27 06:00
PHST- 2018/12/07 00:00 [received]
PHST- 2019/07/19 00:00 [revised]
PHST- 2019/08/20 00:00 [accepted]
PHST- 2019/08/27 06:00 [pubmed]
PHST- 2019/08/27 06:00 [medline]
PHST- 2019/08/27 06:00 [entrez]
AID - 10.1002/humu.23901 [doi]
PST - ppublish
SO  - Hum Mutat. 2020 Jan;41(1):110-114. doi: 10.1002/humu.23901. Epub 2019 Sep 23.
`
