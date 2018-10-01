import { state } from 'cerebral/tags'
import { Compute } from 'cerebral'

export default Compute(state`views.workflows.data.analysis.samples`, (samples) => {
    if (!samples) {
        return []
    }
    const categorizedSamples = []
    const probandSamples = samples.filter((s) => s.proband)
    for (const probandSample of probandSamples) {
        let fatherSample = null
        let motherSample = null
        let siblingSamples = samples.filter((s) => s.sibling_id === probandSample.id)
        if (probandSample.father_id) {
            fatherSample = samples.find((s) => s.id === probandSample.father_id)
            if (!fatherSample) {
                throw Error('Missing father sample in data')
            }
        }
        if (probandSample.mother_id) {
            motherSample = samples.find((s) => s.id === probandSample.mother_id)
            if (!motherSample) {
                throw Error('Missing mother sample in data')
            }
        }
        categorizedSamples.push({
            type: 'proband',
            sample: probandSample
        })
        if (motherSample) {
            categorizedSamples.push({
                type: 'mother',
                sample: motherSample
            })
        }
        if (fatherSample) {
            categorizedSamples.push({
                type: 'father',
                sample: fatherSample
            })
        }
        for (const siblingSample of siblingSamples) {
            categorizedSamples.push({
                type: 'sibling',
                sample: siblingSample
            })
        }
    }

    return categorizedSamples
})
