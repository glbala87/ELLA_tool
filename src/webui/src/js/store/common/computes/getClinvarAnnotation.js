import thenBy from 'thenby'

import { state } from 'cerebral/tags'
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
    let sortVal = '' + sortOrder.indexOf(item.sigText.toLowerCase())
    sortVal += item.lastEvaluated.slice(6) // Year
    sortVal += item.lastEvaluated.slice(3, 5) // Month
    sortVal += item.lastEvaluated.slice(0, 2) // Day

    return -parseInt(sortVal)
}

export default function(allele) {
    return Compute(allele, state`app.config`, (allele, config) => {
        if (!allele || !('CLINVAR' in allele.annotation.external)) {
            return {}
        }
        const revText = allele.annotation.external.CLINVAR['variant_description']
        const clinvar = {
            revText: revText,
            maxStarCount: 4,
            starCount: config.annotation.clinvar.clinical_significance_status[revText],
            items: []
        }
        for (let idx = 0; idx < allele.annotation.external.CLINVAR['items'].length; idx++) {
            let unformatted = allele.annotation.external.CLINVAR['items'][idx]

            // Only show SCV-items
            if (!unformatted.rcv.startsWith('SCV')) {
                continue
            }

            const sigtext = unformatted.clinical_significance_descr
            const phenotypetext = unformatted.traitnames
            const submitter = unformatted.submitter
            const last_evaluated = unformatted.last_evaluated

            const formatted = {
                submitter: submitter === '' ? 'Unknown' : submitter,
                lastEvaluated: last_evaluated === '' ? 'N/A' : last_evaluated,
                sigText: sigtext === '' ? 'No classification' : sigtext,
                phenotypeText: phenotypetext === '' ? 'not specified' : phenotypetext
            }

            clinvar.items.push(formatted)
        }
        clinvar.items.sort(thenBy(sort))
        return clinvar
    })
}
