import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(
    state`modals.addExcludedAlleles.data.alleleIdsByGene`,
    state`modals.addExcludedAlleles.includedAlleleIds`,
    state`modals.addExcludedAlleles.categoryAlleleIds`,
    state`modals.addExcludedAlleles.selectedGene`,
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

        return alleleIds.filter((a) => !includedAlleleIds.includes(a)).sort(
            firstBy((alleleId) => {
                return alleleIdsByGeneCandidates.find((a) => a.allele_ids.includes(alleleId)).symbol
            })
        )
    }
)
