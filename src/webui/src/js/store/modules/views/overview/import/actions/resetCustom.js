import { getAddedState } from '../getImportState'

export default function resetCustom({ state }) {
    state.set('views.overview.import.custom.added', getAddedState())
    state.set(
        'views.overview.import.custom.selectedImportUserGroups',
        state.get('app.user.group.import_groups').slice()
    )
}
