import thenBy from 'thenby'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import getAlleleState from '../../store/modules/views/workflows/interpretation/computed/getAlleleState'
import getAlleleReport from '../../store/modules/views/workflows/interpretation/computed/getAlleleReport'
import getClassification from '../../store/modules/views/workflows/interpretation/computed/getClassification'
import template from './reportcard.ngtmpl.html'

function formatHGVS(allele, classification, config) {
    let hgvs = ''
    for (let t of allele.annotation.filtered) {
        hgvs += `${t.transcript}(${t.symbol}):`
        let hgvs_short = t.HGVSc_short || allele.formatted.hgvsg

        let [type, part] = hgvs_short.split('.')
        if (allele.samples[0].genotype.homozygous) {
            hgvs += `${type}.[${part}];[(${part})]` // c.[76A>C];[(76A>C)]
        } else {
            hgvs += `${type}.[${part}];[=]` // c.[76A>C];[=]
        }
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
    state`views.workflows.data.alleles`,
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
            reportComment: state`views.workflows.interpretation.selected.state.report.comment`,
            readOnly: isReadOnly,
            reportAlleles: getReportAlleleData,
            reportCommentChanged: signal`views.workflows.interpretation.reportCommentChanged`
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
                    }
                })
            }
        ]
    )
})
