import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

const nonsenseConsequences = [
    'start_lost',
    'initiator_codon_variant',
    'transcript_ablation',
    'splice_donor_variant',
    'splice_acceptor_variant',
    'stop_gained',
    'frameshift_variant'
]

export default Compute(state`views.workflows.data.alleles`, alleles => {
    const result = {}
    if (!alleles) {
        return result
    }
    for (let [alleleId, allele] of Object.entries(alleles)) {
        result[alleleId] = allele.annotation.filtered.some(t => {
            return nonsenseConsequences.some(c => {
                return t.consequences.includes(c)
            })
        })
    }
    return result
})
