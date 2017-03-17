/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {AlleleStateHelper} from '../../model/allelestatehelper';

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
        analysis: '=?', // Used for IGV (optional)
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
    }

})
@Inject(
    '$rootScope',
    'Config',
    'Allele',
    'CustomAnnotationModal',
    'IgvModal',
    'Analysis',
    'clipboard',
    'toastr'
)
export class AlleleSectionBoxController {


    constructor(rootScope,
                Config,
                Allele,
                CustomAnnotationModal,
                IgvModal,
                Analysis,
                clipboard,
                toastr) {
        this.config = Config.getConfig();
        this.alleleService = Allele;
        this.customAnnotationModal = CustomAnnotationModal;
        this.igvModal = IgvModal;
        this.analysisService = Analysis;
        this.clipboard = clipboard;
        this.toastr = toastr;

        this.selected_class = null; // Stores selected class in dropdown
        this.calculated_config = null; // calculated at request.

        this.classificationOptions = [{name: 'Unclassified', value: null}].concat(this.config.classification.options);
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

}
