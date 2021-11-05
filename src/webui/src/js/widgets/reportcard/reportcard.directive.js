import thenBy from 'thenby'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import getAlleleState from '../../store/modules/views/workflows/interpretation/computed/getAlleleState'
import getAlleleReport from '../../store/modules/views/workflows/interpretation/computed/getAlleleReport'
import getClassification from '../../store/modules/views/workflows/interpretation/computed/getClassification'
import getEditorReferences from '../../store/modules/views/workflows/interpretation/computed/getEditorReferences'
import template from './reportcard.ngtmpl.html' // eslint-disable-line no-unused-vars

function formatHGVS(allele, classification, config) {
    let hgvs = ''
    for (let t of allele.annotation.filtered) {
        if (t.HGVSc_short) {
            hgvs += `${t.transcript}(${t.symbol}):`
        } else {
            hgvs += `chr${allele.chromosome}(${t.symbol}):`
        }
        let hgvs_short = t.HGVSc_short || allele.formatted.hgvsg

        let [type, part] = hgvs_short.split('.')
        hgvs += `${type}.[];[]`
        if (classification) {
            hgvs += ` ${config.report.classification_text[classification]}`
        }
        hgvs += `\n${hgvs_short}`
        if (t.HGVSp) {
            hgvs += ` ${t.HGVSp}`
        }
        hgvs += '\n\n'
    }
    hgvs += ``
    return hgvs
}

const getReportAlleleData = Compute(
    state`views.workflows.interpretation.data.alleles`,
    state`app.config`,
    (alleles, config, get) => {
        if (!alleles) {
            return
        }
        const result = []

        const includedAlleles = Object.values(alleles).filter((a) => {
            const alleleState = get(getAlleleState(a.id))
            return alleleState.report.included
        })

        includedAlleles.sort(
            thenBy((a) => {
                const classification = get(getClassification(a))
                return config.classification.options.findIndex(
                    (o) => o.value === classification.classification
                )
            }, -1)
                .thenBy((a) => a.annotation.filtered[0].symbol)
                .thenBy((a) => a.annotation.filtered[0].HGVSc_short)
        )

        for (let allele of includedAlleles) {
            const classification = get(getClassification(allele))
            const alleleReport = get(getAlleleReport(allele.id))
            result.push({
                hgvsc: formatHGVS(allele, classification.classification, config),
                comment: alleleReport.evaluation.comment
            })
        }
        return result
    }
)

app.component('reportCard', {
    templateUrl: 'reportcard.ngtmpl.html',
    controller: connect(
        {
            commentTemplates: state`app.commentTemplates`,
            reportComment: state`views.workflows.interpretation.state.report.comment`,
            indicationsComment: state`views.workflows.interpretation.state.report.indicationscomment`,
            readOnly: isReadOnly,
            reportAlleles: getReportAlleleData,
            indicationsCommentChanged: signal`views.workflows.interpretation.indicationsCommentChanged`,
            reportCommentChanged: signal`views.workflows.interpretation.reportCommentChanged`,
            editorReferences: getEditorReferences('report')
        },
        'ReportCard',
        [
            '$scope',
            '$sce',
            ($scope, $sce) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    getReportComment(allele) {
                        return this.sce.trustAsHtml(this.getAlleleReport(allele).evaluation.comment)
                    },
                    getReportIndicationsTemplates() {
                        return $ctrl.commentTemplates['reportIndications']
                    },
                    getReportSummaryTemplates() {
                        return $ctrl.commentTemplates['reportSummary']
                    }
                })
            }
        ]
    )
})
