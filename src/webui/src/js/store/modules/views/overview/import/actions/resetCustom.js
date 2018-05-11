import { getAddedState, getCandidatesState } from '../getImportState'

export default function resetCustom({ state }) {
    state.set('views.overview.import.added', getAddedState())
}
