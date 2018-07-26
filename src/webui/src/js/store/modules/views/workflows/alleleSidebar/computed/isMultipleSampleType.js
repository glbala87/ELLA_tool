import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.alleles`, (alleles) => {
    let types = new Set()
    for (let allele of Object.values(alleles)) {
        for (let t of allele.samples.map((s) => s.sample_type)) {
            types.add(t)
        }
    }

    return types.length > 1
})
