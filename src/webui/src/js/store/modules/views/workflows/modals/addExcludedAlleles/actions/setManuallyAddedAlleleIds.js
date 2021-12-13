import { getManuallyAddedAlleleIdsByCallerType } from '../../../interpretation/computed/getManuallyAddedAlleleIds'

export default function setManuallyAddedAlleleIds({ props, state, resolve }) {
    const { includedAlleleIds } = props
    let stateManuallyIncludedAlleleIds = state
        .get('views.workflows.interpretation.state.manuallyAddedAlleles')
        .slice()

    // Get the current calculated manuallyAddedAlleles to compare
    const currentManuallyAddedAllelesByCallerType = resolve.value(
        getManuallyAddedAlleleIdsByCallerType
    )

    // Add new ones
    for (const alleleId of includedAlleleIds) {
        if (!stateManuallyIncludedAlleleIds.includes(alleleId)) {
            stateManuallyIncludedAlleleIds.push(alleleId)
        }
    }

    // Remove removed ones
    for (const alleleId of currentManuallyAddedAllelesByCallerType) {
        if (!includedAlleleIds.includes(alleleId)) {
            stateManuallyIncludedAlleleIds = stateManuallyIncludedAlleleIds.filter(
                (aId) => aId !== alleleId
            )
        }
    }
    state.set(
        'views.workflows.interpretation.state.manuallyAddedAlleles',
        stateManuallyIncludedAlleleIds
    )
}
