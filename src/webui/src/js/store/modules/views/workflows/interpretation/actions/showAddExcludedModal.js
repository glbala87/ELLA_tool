import getReferenceAssessment from '../computed/getReferenceAssessment'
import isReadOnly from '../../computed/isReadOnly'
import { read } from 'fs'

export default function showAddExcludedModal({ AddExcludedAllelesModal, state, path, resolve }) {
    const analysis = state.get('views.workflows.data.analysis')
    const interpretation = state.get('views.workflows.interpretation.selected')
    const excludedAlleleIds = interpretation.excluded_allele_ids
    const { name: genepanelName, version: genepanelVersion } = state.get(
        'views.workflows.data.genepanel'
    )
    const sampleId = analysis.samples[0].id // TODO: Handle multiple samples
    const includedAlleleIds = interpretation.state.manuallyAddedAlleles || []
    const readOnly = resolve.value(isReadOnly)

    // excluded_allele_ids, included_allele_ids, sample_id, gp_name, gp_version, read_only
    console.log(
        excludedAlleleIds,
        includedAlleleIds,
        sampleId,
        genepanelName,
        genepanelVersion,
        readOnly
    )
    return AddExcludedAllelesModal.show(
        excludedAlleleIds,
        includedAlleleIds,
        sampleId,
        genepanelName,
        genepanelVersion,
        readOnly
    )
        .then((result) => {
            console.log(result)
            if (result) {
                return path.result({ evaluation: result.evaluation })
            }
            return path.dismissed()
        })
        .catch((result) => {
            return path.dismissed()
        })
}
