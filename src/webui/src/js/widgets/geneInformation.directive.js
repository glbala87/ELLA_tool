import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import getGenepanelValuesForGene from '../store/common/computes/getGenepanelValuesForGene'
import template from './geneInformation.ngtmpl.html'

const geneComment = Compute(props`hgncId`, state`views.workflows.data`, (hgncId, data) => {
    console.log(hgncId)
})

app.component('geneInformation', {
    bindings: {
        hgncId: '<',
        hgncSymbol: '<'
    },
    templateUrl: 'geneInformation.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            genepanelValues: getGenepanelValuesForGene(
                props`hgncId`,
                state`views.workflows.interpretation.data.genepanel`,
                props`hgncSymbol`
            )
        },
        'GeneInformation',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    geneCommentEditable: false,
                    editedGeneComment: null,
                    toggleGeneCommentEdit() {
                        $ctrl.geneCommentEditable = !$ctrl.geneCommentEditable
                    },
                    getOmimLink() {
                        const entryId = $ctrl.genepanelValues.omimEntryId
                        return entryId
                            ? `https://www.omim.org/entry/${entryId}`
                            : `https://www.omim.org/search/?search=${$ctrl.hgncSymbol}`
                    },
                    getHgmdLink() {
                        return `https://portal.biobase-international.com/hgmd/pro/gene.php?gene=${$ctrl.hgncSymbol}`
                    },
                    getFrequencyExternal() {
                        return `${$ctrl.genepanelValues.freqCutoffs.value.external.lo_freq_cutoff}/${$ctrl.genepanelValues.freqCutoffs.value.external.hi_freq_cutoff}`
                    },
                    getFrequencyInternal() {
                        return `${$ctrl.genepanelValues.freqCutoffs.value.internal.lo_freq_cutoff}/${$ctrl.genepanelValues.freqCutoffs.value.internal.hi_freq_cutoff}`
                    },
                    getGeneCommentModel() {
                        if ($ctrl.geneCommentEditable) {
                            return $ctrl.editedGeneComment
                        }
                        return $ctrl.message
                    },
                    editClicked() {
                        $ctrl.mode = 'edit'
                        $ctrl.editedMessage = Object.assign({}, $ctrl.message)
                    },
                    editConfirmed() {
                        $ctrl.editMessageClicked({
                            interpretationLog: {
                                id: $ctrl.message.originalId,
                                message: $ctrl.editedMessage.message
                            }
                        })
                        $ctrl.mode = 'normal'
                    },
                    editAborted() {
                        $ctrl.mode = 'normal'
                        $ctrl.editedMessage = null
                    }
                })
            }
        ]
    )
})
