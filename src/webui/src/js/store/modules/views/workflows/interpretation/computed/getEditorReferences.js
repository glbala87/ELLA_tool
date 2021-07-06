import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getReferenceAnnotation from './getReferenceAnnotation'

const CATEGORIES = [
    {
        name: 'Evaluated',
        type: 'evaluated'
    },
    {
        name: 'Pending',
        type: 'pending'
    }
]

export default Compute(
    state`views.workflows.interpretation.data.alleles`,
    state`views.workflows.selectedAllele`,
    state`views.workflows.interpretation.data.references`,
    (alleles, alleleIdSelected, references, get) => {
        const result = []
        if (!references) {
            return result
        }
        // use selected allele, if set - all alleles otherwise
        ;(alleleIdSelected != null ? [alleles[alleleIdSelected]] : Object.values(alleles)).forEach(
            (allele) => {
                for (const category of CATEGORIES) {
                    const { published, unpublished } = get(
                        getReferenceAnnotation(category.type, allele, references)
                    )[category.type]
                    const allReferences = published.concat(unpublished)
                    if (allReferences.length) {
                        result.push({
                            name: category.name,
                            references: allReferences
                        })
                    }
                }
            }
        )
        return result
    }
)
