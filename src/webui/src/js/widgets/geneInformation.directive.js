import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import getGenepanelValues from '../store/common/computes/getGenepanelValues'
import getGeneAssessment from '../store/modules/views/workflows/interpretation/computed/getGeneAssessment'
import template from './geneInformation.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('geneInformation', {
    bindings: {
        hgncId: '<',
        hgncSymbol: '<'
    },
    templateUrl: 'geneInformation.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            genepanelValues: getGenepanelValues(
                state`views.workflows.interpretation.data.genepanel`
            ),
            commentTemplates: state`app.commentTemplates`,
            geneAssessment: getGeneAssessment(props`hgncId`),
            userGeneAssessment: state`views.workflows.interpretation.geneInformation.geneassessment.${props`hgncId`}`,
            geneAssessmentChanged: signal`views.workflows.interpretation.geneAssessmentChanged`,
            undoGeneAssessmentClicked: signal`views.workflows.interpretation.undoGeneAssessmentClicked`,
            updateGeneAssessmentClicked: signal`views.workflows.interpretation.updateGeneAssessmentClicked`
        },
        'GeneInformation',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    getOmimLink() {
                        if ($ctrl.hgncId in $ctrl.genepanelValues) {
                            const entryId = $ctrl.genepanelValues[$ctrl.hgncId].omimEntryId
                            return entryId
                                ? `https://www.omim.org/entry/${entryId}`
                                : `https://www.omim.org/search/?search=${$ctrl.hgncSymbol}`
                        }
                    },
                    getHgmdLink() {
                        return `https://my.qiagendigitalinsights.com/bbp/view/hgmd/pro/gene.php?gene=${$ctrl.hgncSymbol}`
                    },
                    getFrequencyExternal() {
                        if ($ctrl.hgncId in $ctrl.genepanelValues) {
                            const loCutoff =
                                $ctrl.genepanelValues[$ctrl.hgncId].freqCutoffsACMG.value.external
                                    .lo_freq_cutoff
                            const hiCutoff =
                                $ctrl.genepanelValues[$ctrl.hgncId].freqCutoffsACMG.value.external
                                    .hi_freq_cutoff
                            return `${loCutoff}/${hiCutoff}`
                        }
                        return 'N/A'
                    },
                    getFrequencyInternal() {
                        if ($ctrl.hgncId in $ctrl.genepanelValues) {
                            const loCutoff =
                                $ctrl.genepanelValues[$ctrl.hgncId].freqCutoffsACMG.value.internal
                                    .lo_freq_cutoff
                            const hiCutoff =
                                $ctrl.genepanelValues[$ctrl.hgncId].freqCutoffsACMG.value.internal
                                    .hi_freq_cutoff
                            return `${loCutoff}/${hiCutoff}`
                        }
                        return 'N/A'
                    },
                    getGeneCommentModel() {
                        return $ctrl.userGeneAssessment
                            ? $ctrl.userGeneAssessment.evaluation
                            : $ctrl.geneAssessment.evaluation
                    },
                    isCommmentEditable() {
                        // If there's a userGeneAssessment, it's per definition
                        // editable
                        return Boolean($ctrl.userGeneAssessment)
                    },
                    editClicked() {
                        if (!$ctrl.hgncId) {
                            throw Error("Missing property 'hgncId'")
                        }
                        const copiedGeneAssessment = JSON.parse(
                            JSON.stringify($ctrl.geneAssessment)
                        )
                        $ctrl.geneAssessmentChanged({
                            hgncId: $ctrl.hgncId,
                            geneAssessment: copiedGeneAssessment
                        })
                    },
                    geneCommentChanged() {
                        $ctrl.geneAssessmentChanged({
                            hgncId: $ctrl.hgncId,
                            geneAssessment: $ctrl.userGeneAssessment
                        })
                    },
                    undoGeneAssessment() {
                        $ctrl.undoGeneAssessmentClicked({ hgncId: $ctrl.hgncId })
                    },
                    isGeneCommentChanged() {
                        if ($ctrl.geneAssessment && $ctrl.userGeneAssessment) {
                            return (
                                $ctrl.geneAssessment.evaluation.comment !==
                                $ctrl.userGeneAssessment.evaluation.comment
                            )
                        }
                        return false
                    }
                })
            }
        ]
    )
})
