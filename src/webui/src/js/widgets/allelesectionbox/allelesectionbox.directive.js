/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'
import { AlleleStateHelper } from '../../model/allelestatehelper'
import { ACMGHelper } from '../../model/acmghelper'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal, props } from 'cerebral/tags'
import { Compute } from 'cerebral'

import isAlleleAssessmentOutdated from '../../store/common/computes/isAlleleAssessmentOutdated'
import hasExistingAlleleAssessment from '../../store/common/computes/hasExistingAlleleAssessment'
import isAlleleAssessmentReused from '../../store/modules/views/workflows/interpretation/computed/isAlleleAssessmentReused'
import getAlleleAssessment from '../../store/modules/views/workflows/interpretation/computed/getAlleleAssessment'
import getAlleleReport from '../../store/modules/views/workflows/interpretation/computed/getAlleleReport'
import getAlleleState from '../../store/modules/views/workflows/interpretation/computed/getAlleleState'
import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import getReferenceAssessment from '../../store/modules/views/workflows/interpretation/computed/getReferenceAssessment'
import {
    getReferencesIdsForAllele,
    findReferencesFromIds
} from '../../store/common/helpers/reference'

const getExcludedReferencesCount = Compute(
    state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
    state`views.workflows.data.references`,
    (allele, references, get) => {
        if (!allele || !references) {
            return
        }
        const alleleReferenceIds = getReferencesIdsForAllele(allele)
        const alleleReferences = findReferencesFromIds(
            Object.values(references),
            alleleReferenceIds
        ).references
        return alleleReferences
            .map((r) => get(getReferenceAssessment(allele.id, r.id)) || null)
            .filter((ra) => {
                if (ra && 'evaluation' in ra) {
                    return ra.evaluation.relevance === 'Ignore'
                }
                return false
            }).length
    }
)

const getSection = Compute(
    state`views.workflows.selectedComponent`,
    state`views.workflows.components`,
    props`sectionKey`,
    (selectedComponent, components, sectionKey) => {
        if (!selectedComponent) {
            return
        }
        if (selectedComponent in components && components[selectedComponent].sections) {
            return components[selectedComponent].sections[sectionKey]
        }
    }
)

const isCollapsed = Compute(
    state`views.workflows.interpretation.selected.user_state`,
    state`views.workflows.selectedAllele`,
    props`sectionKey`,
    (userState, selectedAllele, sectionKey) => {
        if (!userState || !userState.allele) {
            return
        }
        if (
            selectedAllele in userState.allele &&
            'sections' in userState.allele[selectedAllele] &&
            sectionKey in userState.allele[selectedAllele].sections
        ) {
            return userState.allele[selectedAllele].sections[sectionKey].collapsed
        }
        return false
    }
)

const classificationOptions = Compute(state`app.config`, (config) => {
    return [{ name: 'Select class', value: null }].concat(config.classification.options)
})

app.component('alleleSectionbox', {
    bindings: {
        sectionKey: '<'
    },
    templateUrl: 'ngtmpl/allelesectionbox-new.ngtmpl.html',
    controller: connect(
        {
            classificationOptions,
            collapsed: isCollapsed,
            readOnly: isReadOnly,
            section: getSection,
            selectedAllele: state`views.workflows.selectedAllele`,
            alleleassessment: getAlleleAssessment(state`views.workflows.selectedAllele`),
            allelereport: getAlleleReport(state`views.workflows.selectedAllele`),
            isAlleleAssessmentOutdated: isAlleleAssessmentOutdated(
                state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
            ),
            hasExistingAlleleAssessment: hasExistingAlleleAssessment(
                state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
            ),
            isAlleleAssessmentReused: isAlleleAssessmentReused(
                state`views.workflows.selectedAllele`
            ),
            showExcludedReferences: state`views.workflows.interpretation.selected.user_state.allele.${state`views.workflows.selectedAllele`}.showExcludedReferences`,
            addCustomAnnotationClicked: signal`views.workflows.interpretation.addCustomAnnotationClicked`,
            classificationChanged: signal`views.workflows.interpretation.classificationChanged`,
            collapseAlleleSectionboxChanged: signal`views.workflows.interpretation.collapseAlleleSectionboxChanged`,
            evaluationCommentChanged: signal`views.workflows.interpretation.evaluationCommentChanged`,
            alleleReportCommentChanged: signal`views.workflows.interpretation.alleleReportCommentChanged`,
            reuseAlleleAssessmentClicked: signal`views.workflows.interpretation.reuseAlleleAssessmentClicked`,
            removeAcmgClicked: signal`views.workflows.interpretation.removeAcmgClicked`,
            acmgCodeChanged: signal`views.workflows.interpretation.acmgCodeChanged`,
            showExcludedReferencesClicked: signal`views.workflows.interpretation.showExcludedReferencesClicked`,
            excludedReferenceCount: getExcludedReferencesCount
        },
        'AlleleSectionbox',
        [
            '$scope',
            'cerebral',
            function($scope, cerebral) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    showControls() {
                        if (
                            $ctrl.section.options &&
                            'hideControlsOnCollapse' in $ctrl.section.options
                        ) {
                            return !(
                                $ctrl.section.options.hideControlsOnCollapse && $ctrl.collapsed
                            )
                        }
                    },
                    collapseChangedWrapper(collapsed, section) {
                        $ctrl.collapseAlleleSectionboxChanged({
                            alleleId: $ctrl.selectedAllele,
                            collapsed,
                            section
                        })
                    },
                    getAllelePath() {
                        return `views.workflows.data.alleles.${$ctrl.selectedAllele}`
                    },
                    getCardColor() {
                        return $ctrl.isAlleleAssessmentReused ? 'green' : 'purple'
                    },
                    acmgCodeChangedWrapper(code) {
                        $ctrl.acmgCodeChanged({ alleleId: $ctrl.selectedAllele, code })
                    },
                    getExcludedReferencesBtnText() {
                        return $ctrl.showExcludedReferences
                            ? `HIDE EXCLUDED (${$ctrl.excludedReferenceCount})`
                            : `SHOW EXCLUDED (${$ctrl.excludedReferenceCount})`
                    }
                })
            }
        ]
    )
})

@Directive({
    selector: 'allele-sectionbox-old',
    templateUrl: 'ngtmpl/allelesectionbox.ngtmpl.html',
    scope: {
        header: '=',
        allele: '=',
        references: '=',
        attachments: '=',
        alleleState: '=',
        alleleUserState: '=',
        alleleassessmentComment: '=?', // {name: string, placeholder: string}
        allelereportComment: '=?', // {name: string, placeholder: string}
        section: '=', // Section to display using <allelesectionboxcontent>
        updateText: '@?',
        onUpdate: '&?', // On-update callback function (should refresh allele)
        onChangeClass: '&?', // Callback function when changing class (dropdown)
        onSkip: '&?', // Callback function when clicking 'Skip' button. Enables skip button.
        controls: '=',
        readOnly: '=?' // prevent user from changing/updating if readOnly is true
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
    'ACMGClassificationResource',
    'IgvModal',
    'Analysis',
    'AttachmentResource',
    'clipboard',
    'toastr',
    '$scope'
)
export class AlleleSectionBoxController {
    constructor(
        rootScope,
        Config,
        Allele,
        CustomAnnotationModal,
        ACMGClassificationResource,
        IgvModal,
        Analysis,
        AttachmentResource,
        clipboard,
        toastr,
        $scope
    ) {
        this.config = Config.getConfig()
        this.alleleService = Allele
        this.customAnnotationModal = CustomAnnotationModal
        this.acmgClassificationResource = ACMGClassificationResource
        this.igvModal = IgvModal
        this.analysisService = Analysis
        this.attachmentResource = AttachmentResource
        this.clipboard = clipboard
        this.toastr = toastr

        this.classificationOptions = [{ name: 'Select class', value: null }].concat(
            this.config.classification.options
        )

        // Update suggested classification whenever user changes
        // included ACMG codes
        $scope.$watchCollection(
            () => this.alleleState.alleleassessment.evaluation.acmg.included.map((a) => a.code),
            () => {
                if (this.section.options.show_included_acmg_codes) {
                    this.updateSuggestedClassification()
                }
            }
        )
    }

    getSectionUserState() {
        if (!('sections' in this.alleleUserState)) {
            this.alleleUserState.sections = {}
        }
        if (!(this.section.name in this.alleleUserState.sections)) {
            this.alleleUserState.sections[this.section.name] = {
                collapsed: false
            }
        }
        return this.alleleUserState.sections[this.section.name]
    }

    collapseAll() {
        let section_states = Object.values(this.alleleUserState.sections)
        let current_collapsed = section_states.map((s) => s.collapsed)
        let some_collapsed = current_collapsed.some((c) => c)
        for (let section_state of section_states) {
            section_state.collapsed = !some_collapsed
        }
    }

    showControls() {
        if (this.section.options && 'hide_controls_on_collapse' in this.section.options) {
            return !(
                this.section.options.hide_controls_on_collapse &&
                this.getSectionUserState().collapsed
            )
        }
    }

    /**
     * Whether the card is editable or not. If reusing alleleassessment, user cannot edit the card.
     * Defaults to true if no data.
     * @return {Boolean}
     */
    isEditable() {
        return !this.isAlleleAssessmentReused()
    }

    /**
     * Whether the report comment is editable or not. Even if reusing alleleassessment, the user can edit the comment.
     * The alleleassessment is reused when hitting 'Finish > Finalize'.
     * The purpose is to allow for updating the report comment without changing the classification (classification date).
     * @return {Boolean}
     */
    isReportEditable() {
        return !this.readOnly
    }

    getClassification() {
        return AlleleStateHelper.getClassification(this.allele, this.alleleState)
    }

    getAlleleAssessment() {
        return AlleleStateHelper.getAlleleAssessment(this.allele, this.alleleState)
    }

    getAlleleReport() {
        return AlleleStateHelper.getAlleleReport(this.allele, this.alleleState)
    }

    excludeACMG(code) {
        ACMGHelper.excludeACMG(code, this.allele, this.alleleState)
    }

    getSuggestedClassification() {
        if (this.getAlleleAssessment().evaluation.acmg.suggested_classification) {
            return this.getAlleleAssessment().evaluation.acmg.suggested_classification
        } else {
            return '-'
        }
    }

    updateSuggestedClassification() {
        // Only update data if we're modifying the allele state,
        // we don't want to overwrite anything in any existing allele assessment
        if (AlleleStateHelper.isAlleleAssessmentReused(this.allele, this.alleleState)) {
            return
        }

        // Clear current in case something goes wrong
        // Having no result is better than wrong result
        this.alleleState.alleleassessment.evaluation.acmg.suggested_classification = null
        let codes = this.alleleState.alleleassessment.evaluation.acmg.included.map((i) => i.code)

        if (codes.length) {
            this.acmgClassificationResource
                .getClassification(codes)
                .then((result) => {
                    this.alleleState.alleleassessment.evaluation.acmg.suggested_classification =
                        result.class
                })
                .catch(() => {
                    this.toastr.error(
                        'Something went wrong when updating suggested classification.',
                        null,
                        5000
                    )
                })
        }
    }

    /**
     * If the allele has an existing alleleassessment,
     * check whether it's outdated.
     * @return {Boolean}
     */
    isAlleleAssessmentOutdated() {
        return AlleleStateHelper.isAlleleAssessmentOutdated(this.allele, this.config)
    }

    getCardColor() {
        if (AlleleStateHelper.isAlleleAssessmentReused(this.alleleState)) {
            return 'green'
        }
        return 'purple'
    }

    hasExistingAlleleAssessment() {
        return this.allele.allele_assessment
    }

    isAlleleAssessmentReused() {
        return AlleleStateHelper.isAlleleAssessmentReused(this.alleleState)
    }

    ///////////////
    /// Controls
    ///////////////

    showIgv() {
        this.igvModal.show(this.analysis, this.allele)
    }

    showCustomAnnotationModal(category) {
        let title = category === 'external' ? 'ADD EXTERNAL DB DATA' : 'ADD PREDICTION DATA'
        let placeholder = category === 'external' ? 'CHOOSE DATABASE' : 'CHOOSE PREDICTION TYPE'
        this.customAnnotationModal
            .show(title, placeholder, this.allele, category)
            .then((result) => {
                if (result) {
                    this.onUpdate()
                }
            })
    }

    showAddReferenceModal() {
        let title = 'ADD STUDIES'
        let placeholder = 'Not used'
        this.customAnnotationModal
            .show(title, placeholder, this.allele, 'references')
            .then((result) => {
                if (result) {
                    this.onUpdate()
                }
            })
    }

    showHideExcludedReferences() {
        this.alleleUserState.showExcludedReferences = !this.alleleUserState.showExcludedReferences
    }

    getExcludeReferencesBtnText() {
        return this.alleleUserState.showExcludedReferences ? 'Hide excluded' : 'Show excluded'
    }

    changeClassification() {
        if (this.readOnly) {
            return
        }

        if (this.onChangeClass) {
            this.onChangeClass({ allele: this.allele })
        }
    }

    setClass1() {
        if (this.readOnly) {
            return
        }

        this.alleleState.alleleassessment.classification = '1'
        this.changeClassification()
        if (this.onSkip) {
            this.onSkip()
        }
    }

    setClass2() {
        if (this.readOnly) {
            return
        }

        this.alleleState.alleleassessment.classification = '2'
        this.changeClassification()

        if (this.onSkip) {
            this.onSkip()
        }
    }

    toggleReuseAlleleAssessment() {
        if (this.readOnly) {
            return
        }
        if (
            AlleleStateHelper.toggleReuseAlleleAssessment(
                this.allele,
                this.alleleState,
                this.config
            )
        ) {
            if (this.onSetClass) {
                this.onSetClass({ allele: this.allele })
            }
        }
        this.changeClassification()
    }

    getUpdateText() {
        return this.updateText !== undefined ? this.updateText : 'Set class'
    }
}
