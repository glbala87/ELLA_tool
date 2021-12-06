import thenBy from 'thenby'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import { chrToContigRef } from '../../util.js'
import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import getAlleleState from '../../store/modules/views/workflows/interpretation/computed/getAlleleState'
import getAlleleReport from '../../store/modules/views/workflows/interpretation/computed/getAlleleReport'
import getClassification from '../../store/modules/views/workflows/interpretation/computed/getClassification'
import getEditorReferences from '../../store/modules/views/workflows/interpretation/computed/getEditorReferences'
import template from './reportcard.ngtmpl.html' // eslint-disable-line no-unused-vars

function extractCytoband(allele) {
    if (allele.annotation.cytoband) {
        return `(${allele.annotation.cytoband})`
    } else return ' '
}

function formatSNV(hgvs, allele, annotation, classification_text) {
    hgvs += '\n'
    if (annotation.HGVSc_short) {
        hgvs += `${annotation.transcript}(${annotation.symbol}):`
    }

    let hgvs_short = annotation.HGVSc_short || allele.formatted.hgvsg

    let [type, part] = hgvs_short.split('.')

    hgvs += `${type}.[];[] `
    hgvs += classification_text
    hgvs += `\n${hgvs_short}`

    if (annotation.HGVSp) {
        hgvs += `${annotation.HGVSp}`
    }

    return hgvs
}

function formatCNV(hgvs, allele, annotation, classification_text) {
    hgvs += '\n'
    let hgvs_short = annotation.HGVSc_short || allele.formatted.hgvsg

    hgvs += classification_text
    hgvs += `\n${chrToContigRef(allele.chromosome)}:${hgvs_short}`

    if (annotation.HGVSp) {
        hgvs += `${annotation.HGVSp}`
    }

    hgvs += '\n'
    hgvs += `seq[${allele.genome_reference}] ${allele.change_type}(${
        allele.chromosome
    })${extractCytoband(allele)}`

    return hgvs
}

function formatHGVS(allele, classification, config) {
    let hgvs = ''
    let classification_text = ''

    if (classification) {
        classification_text = `${config.report.classification_text[classification]}`
    }

    for (let annotation of allele.annotation.filtered) {
        if (allele.caller_type === 'snv') {
            hgvs += formatSNV(hgvs, allele, annotation, classification_text)
        } else if (allele.caller_type === 'cnv') {
            hgvs += formatCNV(hgvs, allele, annotation, classification_text)
        } else {
            throw Error(`caller_type not supported: ${allele.caller_type}`)
        }
        hgvs += '\n'
    }
    hgvs += ` `
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
                /** for some big events, vep is not able to produce annotation, therefor we bypass sorting on these */

                .thenBy((a) => {
                    if (
                        a.caller_type === 'cnv' &&
                        (!a.annotation.filtered.length || !a.annotation.filtered[0].symbol)
                    ) {
                        0
                    } else a.annotation.filtered[0].symbol
                })
                .thenBy((a) => {
                    if (
                        a.caller_type === 'cnv' &&
                        (!a.annotation.filtered.length || !a.annotation.filtered[0].HGVSc_short)
                    ) {
                        0
                    } else a.annotation.filtered[0].HGVSc_short
                })
        )

        for (let allele of includedAlleles) {
            const classification = get(getClassification(allele))
            const alleleReport = get(getAlleleReport(allele.id))
            result.push({
                hgvs: formatHGVS(allele, classification.classification, config),
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
