/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {AlleleStateHelper} from '../../model/allelestatehelper';
import {ACMGHelper} from '../../model/acmghelper';

@Directive({
    selector: 'allele-sectionbox',
    templateUrl: 'ngtmpl/allelesectionbox.ngtmpl.html',
    scope: {
        header: '=',
        genepanel: '=',
        allele: '=',
        references: '=',
        alleleState: '=',
        alleleUserState: '=',
        alleleassessmentComment: '=?',  // {name: string, placeholder: string}
        allelereportComment: '=?',  // {name: string, placeholder: string}
        section: '=',  // Section to display using <allelesectionboxcontent>
        updateText: '@?',
        onUpdate: '&?',  // On-update callback function (should refresh allele)
        onChangeClass: '&?',  // Callback function when changing class (dropdown)
        onSkip: '&?', // Callback function when clicking 'Skip' button. Enables skip button.
        controls: '=',
        readOnly: '=?', // prevent user from changing/updating if readOnly is true
        // possible controls: {
        //   toggle_technical: bool,
        //   toggle_class2: bool,
        //   skip_next: bool,
        //   checked: bool,
        //   classification: bool,
        //   vardb: bool,
        //   custom_prediction: bool,
        //   custom_external: bool
        //}
        //
    },
})
@Inject(
    '$rootScope',
    'Config',
    'Allele',
    'CustomAnnotationModal',
    'ACMGClassificationResource',
    'IgvModal',
    'Analysis',
    'clipboard',
    'toastr',
    '$scope'
)
export class AlleleSectionBoxController {


    constructor(rootScope,
                Config,
                Allele,
                CustomAnnotationModal,
                ACMGClassificationResource,
                IgvModal,
                Analysis,
                clipboard,
                toastr,
                $scope) {
        this.config = Config.getConfig();
        this.alleleService = Allele;
        this.customAnnotationModal = CustomAnnotationModal;
        this.acmgClassificationResource = ACMGClassificationResource;
        this.igvModal = IgvModal;
        this.analysisService = Analysis;
        this.clipboard = clipboard;
        this.toastr = toastr;

        this.classificationOptions = [{name: 'Unclassified', value: null}].concat(this.config.classification.options);

        // Update suggested classification whenever user changes
        // included ACMG codes
        $scope.$watchCollection(
            () => this.alleleState.alleleassessment.evaluation.acmg.included.map(a => a.code),
            () => {
                if (this.section.options.show_included_acmg_codes) {
                    this.updateSuggestedClassification();
                }
            }
        );

        this.pathogenicPopoverToggle = {
          buttons: [ 'Pathogenic', 'Benign' ],
          model: 'Pathogenic'
        };

        this.popover = {
            templateUrl: 'ngtmpl/acmgSelectionPopover.ngtmpl.html'
        };

        this.setACMGCandidates();
    }

    getSectionUserState() {
        if (!('sections' in this.alleleUserState)) {
            this.alleleUserState.sections = {};
        }
        if (!(this.section.name in this.alleleUserState.sections)) {
            this.alleleUserState.sections[this.section.name] = {
                collapsed: false
            }
        }
        return this.alleleUserState.sections[this.section.name];
    }

    collapseAll() {
        let section_states = Object.values(this.alleleUserState.sections);
        let current_collapsed = section_states.map(s => s.collapsed);
        let some_collapsed = current_collapsed.some(c => c);
        for (let section_state of section_states) {
            section_state.collapsed = !some_collapsed;
        }
    }

    showControls() {
        if (this.section.options &&
            'hide_controls_on_collapse' in this.section.options) {
            return !(this.section.options.hide_controls_on_collapse &&
                        this.getSectionUserState().collapsed);
        }
    }

    /**
     * Whether the card is editable or not. If reusing alleleassessment, user cannot edit the card.
     * Defaults to true if no data.
     * @return {Boolean}
     */
    isEditable() {
        return !this.isAlleleAssessmentReused();
    }

    getClassification() {
        return AlleleStateHelper.getClassification(this.allele, this.alleleState);
    }

    getAlleleAssessment() {
        return AlleleStateHelper.getAlleleAssessment(this.allele, this.alleleState);
    }

    getAlleleReport() {
        return AlleleStateHelper.getAlleleReport(this.allele, this.alleleState);
    }

    excludeACMG(code) {
        ACMGHelper.excludeACMG(code, this.allele, this.alleleState);
    }

    getSuggestedClassification() {
        if (this.getAlleleAssessment().evaluation.acmg.suggested_classification) {
            return this.getAlleleAssessment().evaluation.acmg.suggested_classification;
        } else {
            return "-";
        }
    }

    updateSuggestedClassification() {
        // Only update data if we're modifying the allele state,
        // we don't want to overwrite anything in any existing allele assessment
        if (AlleleStateHelper.isAlleleAssessmentReused(this.allele, this.alleleState)) {
            return;
        }

        // Clear current in case something goes wrong
        // Having no result is better than wrong result
        this.alleleState.alleleassessment.evaluation.acmg.suggested_classification = null;
        let codes = this.alleleState.alleleassessment.evaluation.acmg.included.map(i => i.code);

        if (codes.length) {
            this.acmgClassificationResource.getClassification(codes).then(result => {
                this.alleleState.alleleassessment.evaluation.acmg.suggested_classification = result.class;
            }).catch(() => {
                this.toastr.error("Something went wrong when updating suggested classification.", null, 5000);
            });
        }
    }

    /**
     * If the allele has an existing alleleassessment,
     * check whether it's outdated.
     * @return {Boolean}
     */
    isAlleleAssessmentOutdated() {
        return AlleleStateHelper.isAlleleAssessmentOutdated(this.allele, this.config);
    }

    getCardColor() {
        if (this.isAlleleAssessmentReused()) {
                return 'yellow';
        }
        return 'blue';
    }

    hasExistingAlleleAssessment() {
        return this.allele.allele_assessment;
    }

    isAlleleAssessmentReused() {
        return AlleleStateHelper.isAlleleAssessmentReused(this.alleleState);
    }

    ///////////////
    /// Controls
    ///////////////

    showIgv() {
        this.igvModal.show(this.analysis, this.allele);
    }

    showCustomAnnotationModal(category) {
        let title = category === 'external' ? 'ADD EXTERNAL DB DATA' : 'ADD PREDICTION DATA';
        let placeholder = category === 'external' ? 'CHOOSE DATABASE' : 'CHOOSE PREDICTION TYPE';
        this.customAnnotationModal.show(title, placeholder, [this.allele], category).then(result => {
            if (result) {
                if (this.onUpdate) {
                    this.onUpdate();
                }
            }
        });
    }

    showAddReferenceModal() {
        let title = 'ADD REFERENCES';
        let placeholder = "Not used";
        this.customAnnotationModal.show(title, placeholder, [this.allele], 'references').then(result => {
            if (result) {
                if (this.onUpdate) {
                    this.onUpdate();
                }
            }
        });
    }

    showHideExcludedReferences() {
        this.alleleUserState.showExcludedReferences = !this.alleleUserState.showExcludedReferences;
    }

    getExcludeReferencesBtnText() {
        return this.alleleUserState.showExcludedReferences ? "Hide excluded" : "Show excluded"
    }

    changeClassification() {
        if (this.readOnly) {
            return;
        }

        if (this.onChangeClass) {
            this.onChangeClass({allele: this.allele});
        }
    }

    setClass1() {
        if (this.readOnly) {
            return;
        }

        this.alleleState.alleleassessment.classification = '1';
        this.changeClassification();
        if (this.onSkip) {
            this.onSkip();
        }
    }

    setClass2() {
        if (this.readOnly) {
            return;
        }

        this.alleleState.alleleassessment.classification = '2';
        this.changeClassification();

        if (this.onSkip) {
            this.onSkip();
        }
    }

    setTechnical() {
        if (this.readOnly) {
            return;
        }

        this.alleleState.alleleassessment.classification = 'T';
        this.changeClassification();

        if (this.onSkip) {
            this.onSkip();
        }
    }

    toggleReuseAlleleAssessment() {
        if (this.readOnly) {
            return;
        }
        if (AlleleStateHelper.toggleReuseAlleleAssessment(this.allele, this.alleleState, this.config)) {
            if (this.onSetClass) {
                this.onSetClass({allele: this.allele});
            }
        }
        this.changeClassification();
    }

    getUpdateText() {
        return this.updateText !== undefined ? this.updateText : 'Set class';
    }

    copyAlamut() {
        this.clipboard.copyText(this.allele.formatAlamut());
        this.toastr.info('Copied text to clipboard', null, {timeOut: 1000});
    }


    ///////////////
    /// ACMG popover
    ///////////////

    /**
     * Create list of ACMG code candidates for showing
     * in popover. Sorts the codes into array of arrays,
     * one array for each group.
     */
    setACMGCandidates() {
        this.acmgCandidates = {};

        let candidates = Object.keys(this.config.acmg.explanation).filter(code => !code.startsWith('REQ'));

        for (let t of ['benign', 'pathogenic']) {
            this.acmgCandidates[t] = [];

            // Map codes to group (benign/pathogenic)
            for (let c of candidates) {
                if (this.config.acmg.codes[t].some(e => c.startsWith(e))) {
                    if (!this.acmgCandidates[t].includes(c)) {
                        this.acmgCandidates[t].push(c);
                    }
                }
            }

            // Sort the codes
            this.acmgCandidates[t].sort((a, b) => {
                // Find the difference in index between the codes
                let a_idx = this.config.acmg.codes[t].findIndex(elem => a.startsWith(elem));
                let b_idx = this.config.acmg.codes[t].findIndex(elem => b.startsWith(elem));

                // If same prefix, sort on text itself
                if (a_idx === b_idx) {
                    return a.localeCompare(b);
                }
                return a_idx - b_idx;
            });
            // Pull out any codes with an 'x' in them, and place them next after their parent code
            // This bugs out for a few codes that don't have parents, but is good enough for now
            let x_codes = [];
            x_codes = this.acmgCandidates[t].filter( (e) => { if(e.includes('x')) { return true; } } );
            x_codes.forEach( (e) => { this.acmgCandidates[t].splice(this.acmgCandidates[t].indexOf(e),1) } );
            x_codes.forEach( (e) => {
              this.acmgCandidates[t].splice(
                (this.acmgCandidates[t].indexOf(e.split('x')[1])+1),
                0, e
              )
            })
        }
    }

    getExplanationForCode(code) {
        return this.config.acmg.explanation[code];
    }

    getACMGpopoverClass(code) {
      let acmgclass = this.getACMGClass(code);
      return code.includes('x') ? `indented ${acmgclass}` : acmgclass;
    }

    /**
     * Lets user include a code not provided by backend.
     * @param {String} code Code to add
     */
    addStagedACMGCode() {
        if (this.staged_code) {
            this.includeACMG(this.staged_code);
        }
        this.staged_code = null;
    }

    /**
     * "Stages" an ACMG code in the popover, for editing before adding it.
     * @param {String} code Code to add
     */
    stageACMGCode(code) {
        let existing_comment = this.staged_code ? this.staged_code.comment : '';
        this.staged_code = ACMGHelper.userCodeToObj(code, existing_comment);
    }

    getACMGClass(code) {
        return code.substring(0, 2).toLowerCase();
    }

    includeACMG(code) {
        ACMGHelper.includeACMG(code, this.allele, this.alleleState);
    }


}
