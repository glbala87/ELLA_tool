import { getAddedState } from '../getImportState'

export default function resetCustom({ state }) {
    state.set('views.overview.import.custom.added', getAddedState())
}
