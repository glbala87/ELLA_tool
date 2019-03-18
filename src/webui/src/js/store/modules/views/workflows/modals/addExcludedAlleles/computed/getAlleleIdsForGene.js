import thenBy from 'thenby'
import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(
    state`views.workflows.modals.addExcludedAlleles.data.alleleIdsByGene`,
    state`views.workflows.modals.addExcludedAlleles.includedAlleleIds`,
    state`views.workflows.modals.addExcludedAlleles.categoryAlleleIds`,
    state`views.workflows.modals.addExcludedAlleles.selectedGene`,
    (alleleIdsByGene, includedAlleleIds, categoryAlleleIds, selectedGene) => {
        if (!alleleIdsByGene || !includedAlleleIds || !categoryAlleleIds) {
            return []
        }

        let alleleIds = categoryAlleleIds.slice()
        let alleleIdsByGeneCandidates = alleleIdsByGene
        if (selectedGene) {
            alleleIdsByGeneCandidates = alleleIdsByGene.filter((a) => a.symbol === selectedGene)
            alleleIds = alleleIds.filter((alleleId) => {
                return alleleIdsByGeneCandidates.some((a) => a.allele_ids.includes(alleleId))
            })
        }

        // Remove any already included ids

        return alleleIds
            .filter((a) => !includedAlleleIds.includes(a))
            .sort(
                thenBy((alleleId) => {
                    const entry = alleleIdsByGeneCandidates.find((a) =>
                        a.allele_ids.includes(alleleId)
                    )
                    return entry ? entry.symbol : ''
                })
            )
    }
)
