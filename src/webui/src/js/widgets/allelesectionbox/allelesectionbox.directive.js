/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {AlleleStateHelper} from '../../model/allelestatehelper';

@Directive({
    selector: 'allele-sectionbox',
    templateUrl: 'ngtmpl/allelesectionbox.ngtmpl.html',
    scope: {
        title: '=',
        genepanel: '=',
        allele: '=',
        references: '=',
        alleleState: '=',
        alleleUserState: '=',
        comments: '=',  // Array of [{model: string, placeholder: string}, ...]
        section: '=',  // Section to display using <allelesectionboxcontent>
        updateText: '@?',
        onUpdate: '&?',  // On-update callback function (should refresh allele)
        onSetClass: '&?',  // Callback function when clicking 'Set' button for setting class
        onSkip: '&?', // Callback function when clicking 'Skip' button. Enables skip button.
        //controls: {
        //   class2: bool,
        //   checked: bool,
        //   classification: bool,
        //   vardb: bool,
        //   custom_prediction: bool,
        //   custom_external: bool
        //}
        //
        controls: '=',
        // options: {
        //    collapsed: bool,
        //    expanded: bool
        // }
        options: '='
        //
    }

})
@Inject(
    'Config',
    'Allele',
    'CustomAnnotationModal',
    'Analysis',
    'Interpretation'
)
export class AlleleSectionBoxController {


    constructor(Config,
                Allele,
                CustomAnnotationModal,
                Analysis,
                Interpretation) {
        this.config = Config.getConfig();
        this.alleleService = Allele;
        this.customAnnotationModal = CustomAnnotationModal;
        this.interpretationService = Interpretation;
        this.analysisService = Analysis;

        this.selected_class = null; // Stores selected class in dropdown
        this.calculated_config = null; // calculated at request.

        this.classificationOptions = this.config.classification.options;
    }


    getInheritanceCodes(geneSymbol) {
        return this.genepanel.getInheritanceCodes(geneSymbol);
    }

    phenotypesBy(geneSymbol) {
        return this.genepanel.phenotypesBy(geneSymbol);
    }

    getGenepanelValues(geneSymbol) {
        //  Cache calculation; assumes this card is associated with only one gene symbol
        if (! this.calculated_config) {
            this.calculated_config = this.genepanel.calculateGenepanelConfig(geneSymbol, this.config.variant_criteria.genepanel_config);
        }
        return this.calculated_config;
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

    isAlleleAssessmentReused() {
        return AlleleStateHelper.isAlleleAssessmentReused(this.alleleState);
    }

    ///////////////
    /// Controls
    ///////////////

    showCustomAnnotationModal(category) {
        let title = category === 'external' ? 'ADD EXTERNAL ANNOTATION' : 'ADD PREDICTION ANNOTATION';
        title += ': ' + this.allele.toString();
        this.customAnnotationModal.show(title, [this.allele], category).then(result => {
            if (result) {
                if (this.onUpdate) {
                    this.onUpdate();
                }
            }
        });
    }

    showAddReferenceModal() {
        let title = 'ADD REFERENCES: ' + this.allele.toString();
        this.customAnnotationModal.show(title, [this.allele], 'references').then(result => {
            if (result) {
                if (this.onUpdate) {
                    this.onUpdate();
                }
            }
        });
    }

    updateClassification() {
        AlleleStateHelper.updateClassification(this.alleleState, this.selected_class);

        if (this.onSetClass) {
            this.onSetClass({allele: this.allele});
        }
    }

    toggleClass2() {
        AlleleStateHelper.toggleClass2(this.alleleState);

        if (this.onSkip) {
            this.onSkip();
        }
    }

    toggleTechnical() {
        AlleleStateHelper.toggleTechnical(this.alleleState);

        if (this.onSkip) {
            this.onSkip();
        }
    }

    toggleReuseAlleleAssessment() {
        if (AlleleStateHelper.toggleReuseAlleleAssessment(this.allele, this.alleleState, this.config)) {
            if (this.onSetClass) {
                this.onSetClass({allele: this.allele});
            }
        };
    }

    getUpdateText() {
        return this.updateText !== undefined ? this.updateText : 'Set class';
    }

}
