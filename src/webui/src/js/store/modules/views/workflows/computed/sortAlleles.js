import { Compute } from 'cerebral'
import { state, props } from 'cerebral/tags'
import { AlleleStateHelper } from '../../../../../model/allelestatehelper'
import getClassification from '../interpretation/computed/getClassification'

export default function sortAlleles(alleles) {
    return Compute(alleles, state`app.config`, (alleles, config, get) => {
        let sortFunc = firstBy(a => {
            let classification = get(getClassification(a.id))
            return config.classification.options.findIndex(o => o.value === classification)
        }, -1)
            .thenBy(a => a.formatted.inheritance)
            .thenBy(a => a.annotation.filtered[0].symbol)
            .thenBy(a => a.start_position)

        const sortedAlleles = Object.values(alleles)
        sortedAlleles.sort(sortFunc)
        return sortedAlleles
    })
}
