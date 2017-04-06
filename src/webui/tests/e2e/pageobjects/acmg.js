let Page = require('./page');
let util = require('./util');

const SELECTOR_TOP = '.id-acmg-container';
const SELECTOR_SUGGESTED = '.id-acmg-suggested';
const SELECTOR_SUGGESTED_REQ = '.id-acmg-suggested-req';
const SELECTOR_SHOW_HIDE = '.id-acmg-show-hide-req';


/**
 * The ACMG content box on the variant/sample interpretation page
 */
class Acmg {

    get showHideBtn() {
        return util.elementOrNull(`${SELECTOR_TOP} ${SELECTOR_SHOW_HIDE}`);
    }
    get suggestedElement() {
        return util.elementOrNull(`${SELECTOR_TOP} ${SELECTOR_SUGGESTED}`);
    }

    get suggestedReqElement() {
        return util.elementOrNull(`${SELECTOR_TOP} ${SELECTOR_SUGGESTED_REQ}`);
    }

    hasShowHideButton() {
        return browser.isExisting(`${SELECTOR_SHOW_HIDE}`);
    }

}

module.exports = new Acmg();
