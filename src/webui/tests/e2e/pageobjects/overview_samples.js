var Page = require('./page');

const SELECTOR_ANALYSES_OVERVIEW = '#id-overview-sidenav-analyses-by-findings'
const SELECTOR_FINISHED = '.id-analysis-finished';
const SELECTOR_EMPTY = '.id-analysis-assessments-none';
const SELECTOR_ASSESSMENTS_MISSING = '.id-analysis-missing-classifications';
const SELECTOR_PENDING = SELECTOR_ASSESSMENTS_MISSING;
const SELECTOR_REVIEW_FINDINGS = '.id-analysis-review-with-findings';
const SELECTOR_REVIEW_NORMAL = '.id-analysis-review-without-findings';
const SELECTOR_REVIEW_ASSESSMENTS_MISSING = '.id-analysis-review-missing-classifications';
const SELECTOR_REVIEW = SELECTOR_REVIEW_ASSESSMENTS_MISSING;
const SELECTOR_MEDICALREVIEW = '.id-analysis-medicalreview';
const SELECTOR_NORMAL =  '.id-analysis-findings-normal';
const SELECTOR_FINDINGS = '.id-analysis-findings';

//id-analysis-ours
// id-analysis-others

const SELECTOR_ANALYSIS_NAME = ".id-analysis-name";

const SECTION_EXPAND_SELECTOR  = " header .sb-title-container";

class SampleSelection extends Page {

    open() {
        super.open('overview/');
        browser.waitForExist(SELECTOR_ANALYSES_OVERVIEW);
        browser.click(SELECTOR_ANALYSES_OVERVIEW);
    }

    get analysisList() { return browser.element('analysis-list') }
    get noFindingsSection() { return browser.element('.id-analysis-findings-none') }
    get findingsSection() { return browser.element(SELECTOR_FINDINGS) }
    get emptySection() { return browser.element(SELECTOR_EMPTY) };
    get pendingSection() { return browser.element(SELECTOR_PENDING) }
    get reviewSection() { return browser.element(SELECTOR_REVIEW) }
    get finishedSection() { return browser.element(SELECTOR_FINISHED) }



    get normalSection() { return browser.element(SELECTOR_NORMAL) }

    expandPendingSection() {
        this._expandSection(SELECTOR_PENDING);
    }

    expandReviewSection() {
        this._expandSection(SELECTOR_REVIEW);
    }

    _expandSection(sectionSelector) {
        this.open();
        browser.waitForExist(sectionSelector);
        // Expand if collapsed
        if (browser.element(sectionSelector+" .collapsed")) {
            browser.click(sectionSelector + SECTION_EXPAND_SELECTOR);
        }
    }

    selectItemInSection(number, sectionSelector) {
        this.open();
        // expand box:
        browser.waitForExist(sectionSelector)

        // Expand if collapsed
        if (browser.element(sectionSelector+" .collapsed")) {
            browser.click(sectionSelector + SECTION_EXPAND_SELECTOR);
        }
        let selector = `${sectionSelector} .id-analysis:nth-child(${number})`;
        // console.log('Going to click selector:' + selector);
        browser.waitForExist(selector);
        browser.click(selector);
        let element = browser.element(selector);
        browser.waitForExist('analysis-list', 5000, true);
        return element;
    }

    selectFinished(number) {
        this.selectItemInSection(number, SELECTOR_FINISHED);
    }

    selectPending(number, name) {
        let analysisWrapper = this.selectItemInSection(number, SELECTOR_PENDING);
        // attempt to validate the chosen element matches the name:
        // This fails with a Cannot read property 'ELEMENT' of null
        // let analysisNameElement = analysisWrapper.element(SELECTOR_ANALYSIS_NAME);
        //
        // if (name) {
        //     actualName = analysisNameElement.getText();
        //     if (name === actualName) {
        //         OK
            // } else {
            //     console.error("Analysis name mismatch");
            // }
        // }

    }

    selectWithMissingAssessments(number, name) {
        let analysisWrapper = this.selectItemInSection(number, SELECTOR_ASSESSMENTS_MISSING);
    }

    selectReview(number) {
        this.selectItemInSection(number, SELECTOR_REVIEW);
    }

    selectMedicalReview(number) {
        this.selectItemInSection(number, SELECTOR_MEDICALREVIEW);
    }

    selectFindingsNormal(number) {
        this.selectItemInSection(number, SELECTOR_NORMAL);
    }

    selectFindings(number) {
        this.selectItemInSection(number, SELECTOR_FINDINGS);
    }

    selectTopPending() {
        this.selectPending(1);
    }

    selectTopReview() {
        this.selectReview(1);
    }

    selectTopMedicalReview() {
        this.selectMedicalReview(1);
    }

    getReviewTags() { // no ui showing tags!
        return browser.getText(`${SELECTOR_REVIEW} .analysis-extras .tag`)
    }

    getReviewComment() {
        let selector = `${SELECTOR_REVIEW} .analysis-extras .id-analysis-comment`;
        return browser.getText(selector)
    }

}

module.exports = SampleSelection;
