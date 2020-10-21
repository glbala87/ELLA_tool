import app from '../ng-decorators'
import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import { connect } from '@cerebral/angularjs'
import getWarnings from '../store/modules/views/workflows/interpretation/computed/getWarnings'

import template from './alleleCollisions.ngtmpl.html'

const getCollisions = (allele) => {
    return Compute(
        allele,
        state`views.workflows.data.collisions`,
        state`app.user`,
        (allele, collisions, user) => {
            if (!allele || !collisions) {
                return []
            }

            let result = []
            for (const c of collisions.filter((c) => c.allele_id === allele.id)) {
                const typeText =
                    c.type === 'analysis'
                        ? `in another analysis: ${c.analysis_name}`
                        : 'in variant workflow'
                const unfinishedTypeText =
                    c.type === 'analysis' ? `an analysis: ${c.analysis_name}` : 'a variant workflow'

                if (c.user) {
                    result.push({
                        message: `This variant is currently being worked on by ${c.user.full_name} ${typeText}.`
                    })
                } else {
                    result.push({
                        message: `This variant is currently waiting in ${c.workflow_status.toUpperCase()} in ${unfinishedTypeText}.`
                    })
                }
            }

            return result
        }
    )
}

app.component('alleleCollisions', {
    templateUrl: 'alleleCollisions.ngtmpl.html',
    controller: connect(
        {
            collisions: getCollisions(
                state`views.workflows.interpretation.data.alleles.${state`views.workflows.selectedAllele`}`
            )
        },
        'AlleleCollisions'
    )
})
