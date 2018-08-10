import thenBy from 'thenby'

import { state, props, string } from 'cerebral/tags'
import { Compute } from 'cerebral'

function sort(item) {
    // Sort by clinical signifiance, then date
    let sortOrder = [
        'benign',
        'likely benign',
        'uncertain significance',
        'likely pathogenic',
        'pathogenic'
    ]
    let sortVal = '' + sortOrder.indexOf(item.sigtext.toLowerCase())
    sortVal += item.last_evaluated.slice(6) // Year
    sortVal += item.last_evaluated.slice(3, 5) // Month
    sortVal += item.last_evaluated.slice(0, 2) // Day

    return -parseInt(sortVal)
}

export default function(allele) {
    return Compute(allele, state`app.config`, (allele, config) => {
        if (!allele || !('CLINVAR' in allele.annotation.external)) {
            return {}
        }
        const revText = allele.annotation.external.CLINVAR['variant_description']
        const clinvar = {
            maxstars: new Array(4),
            revtext: revText,
            revstars: config.annotation.clinvar.clinical_significance_status[revText],
            items: []
        }
        for (let idx = 0; idx < allele.annotation.external.CLINVAR['items'].length; idx++) {
            let unformatted = allele.annotation.external.CLINVAR['items'][idx]

            // Only show SCV-items
            if (!unformatted.rcv.startsWith('SCV')) {
                continue
            }

            let formatted = {}

            let sigtext = unformatted.clinical_significance_descr
            let phenotypetext = unformatted.traitnames
            let submitter = unformatted.submitter
            let last_evaluated = unformatted.last_evaluated

            formatted['submitter'] = submitter === '' ? 'Unknown' : submitter
            formatted['last_evaluated'] = last_evaluated === '' ? 'N/A' : last_evaluated
            formatted['sigtext'] = sigtext === '' ? 'No classification' : sigtext
            formatted['phenotypetext'] = phenotypetext === '' ? 'not specified' : phenotypetext

            clinvar.items.push(formatted)
        }
        clinvar.items.sort(thenBy(sort))
        return clinvar
    })
}
