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

const MODE_REPORT = 'report'
const MODE_SELECTED = 'selected'

export default (mode = MODE_SELECTED) => {
    return Compute(
        mode,
        state`views.workflows.interpretation.data.alleles`,
        state`views.workflows.selectedAllele`,
        state`views.workflows.interpretation.state.allele`,
        state`views.workflows.interpretation.data.references`,
        (mode, alleles, alleleIdSelected, allelesState, references, get) => {
            const result = []
            if (!references) {
                return result
            }
            const _getAllelesSelected = (alleles, alleleIdSelected) => {
                // current selected allele
                return alleleIdSelected !== null ? [alleles[alleleIdSelected]] : []
            }
            const _getAllelesReport = (alleles, _, allelesState) => {
                // alleles that are included in the report
                const alleleIdsIncluded = Object.entries(allelesState)
                    .filter(([_, v]) => v.report && v.report.included)
                    .map(([k, _]) => parseInt(k))
                return Object.values(alleles).filter((a) => alleleIdsIncluded.includes(a.id))
            }
            const _getAlleles = mode == MODE_REPORT ? _getAllelesReport : _getAllelesSelected
            _getAlleles(alleles, alleleIdSelected, allelesState).forEach((allele) => {
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
            })
            return result
        }
    )
}
