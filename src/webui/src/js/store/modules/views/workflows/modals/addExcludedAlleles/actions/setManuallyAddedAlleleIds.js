import getManuallyAddedAlleleIds from '../../../interpretation/computed/getManuallyAddedAlleleIds'

export default function setManuallyAddedAlleleIds({ props, state, resolve }) {
    const { includedAlleleIds } = props

    let callerTypeSelected = state.get('views.workflows.alleleSidebar.callerTypeSelected')

    let stateManuallyIncludedAlleleIds = state
        .get('views.workflows.interpretation.state.manuallyAddedAlleles')
        [callerTypeSelected].slice()

    // Get the current calculated manuallyAddedAlleles to compare
    const currentManuallyAddedAlleles = resolve.value(getManuallyAddedAlleleIds)

    // Add new ones
    for (const alleleId of includedAlleleIds) {
        if (!stateManuallyIncludedAlleleIds.includes(alleleId)) {
            stateManuallyIncludedAlleleIds.push(alleleId)
        }
    }

    // Remove removed ones
    for (const alleleId of currentManuallyAddedAlleles) {
        if (!includedAlleleIds.includes(alleleId)) {
            stateManuallyIncludedAlleleIds = stateManuallyIncludedAlleleIds.filter(
                (aId) => aId !== alleleId
            )
        }
    }

    let manuallyAddedAlleleIdPath = `views.workflows.interpretation.state.manuallyAddedAlleles.${callerTypeSelected}`
    state.set(manuallyAddedAlleleIdPath, stateManuallyIncludedAlleleIds)
}
