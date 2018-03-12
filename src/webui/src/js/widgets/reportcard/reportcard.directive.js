/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'
import { AlleleStateHelper } from '../../model/allelestatehelper'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import getAlleleState from '../../store/modules/views/workflows/interpretation/computed/getAlleleState'
import getAlleleReport from '../../store/modules/views/workflows/interpretation/computed/getAlleleReport'
import getClassification from '../../store/modules/views/workflows/interpretation/computed/getClassification'

function formatHGVS(allele, classification, config) {
    let hgvs = ''
    for (let t of allele.annotation.filtered) {
        hgvs += `${t.transcript}(${t.symbol}):`
        let hgvs_short = t.HGVSc_short || allele.getHGVSgShort()

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
        const result = []

        const includedAlleles = Object.values(alleles).filter(a => {
            const alleleState = get(getAlleleState(a.id))
            return alleleState.report.included
        })

        includedAlleles.sort(
            firstBy(a => {
                const classification = get(getClassification(a.id, true))
                return config.classification.options.findIndex(o => o.value === classification)
            }, -1)
                .thenBy(a => a.annotation.filtered[0].symbol)
                .thenBy(a => a.annotation.filtered[0].HGVSc_short)
        )

        for (let allele of includedAlleles) {
            const classification = get(getClassification(allele.id, true))
            const alleleReport = get(getAlleleReport(allele.id))
            result.push({
                hgvsc: formatHGVS(allele, classification, config),
                comment: alleleReport.evaluation.comment
            })
        }
        return result
    }
)

app.component('reportCard', {
    templateUrl: 'ngtmpl/reportcard-new.ngtmpl.html',
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

@Directive({
    selector: 'report-card-old',
    templateUrl: 'ngtmpl/reportcard.ngtmpl.html',
    scope: {
        alleles: '=',
        references: '=',
        state: '=',
        userState: '=',
        readOnly: '=?'
    }
})
@Inject('Config', '$sce')
export class ReportCardController {
    constructor(Config, $sce) {
        this.config = Config.getConfig()
        this.sce = $sce
        this.selected_excluded = null
    }

    getAlleleState(allele) {
        return this.state.allele[allele.id]
    }

    getAlleleReport(allele) {
        return AlleleStateHelper.getAlleleReport(allele, this.getAlleleState(allele))
    }

    getClassification(allele) {
        return AlleleStateHelper.getClassification(allele, this.getAlleleState(allele))
    }

    getAlleleReportComment(allele) {
        return this.sce.trustAsHtml(this.getAlleleReport(allele).evaluation.comment)
    }

    getAlleles() {
        this.alleles.sort(
            firstBy(a => {
                let classification = AlleleStateHelper.getClassification(a, this.getAlleleState(a))
                return this.config.classification.options.findIndex(o => o.value === classification)
            }, -1)
                .thenBy(a => a.annotation.filtered[0].symbol)
                .thenBy(a => a.annotation.filtered[0].HGVSc_short || a.getHGVSgShort())
        )
        return this.alleles
    }

    formatHGVS(allele) {}
}
