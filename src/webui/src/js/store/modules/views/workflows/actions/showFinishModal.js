import { canFinalize } from '../../../../common/helpers/workflow'

class ConfirmCompleteInterpretationController {
    constructor(canFinalize, modalInstance) {
        this.canFinalize = canFinalize
        this.modal = modalInstance
    }
}

// TODO: $uibModal is only temporary until we get rid of angular modals
export default function showFinishModal({ state, $uibModal, path }) {
    const interpretation = state.get('views.workflows.interpretation.selected')
    const alleles = state.get('views.workflows.data.alleles')
    const config = state.get('app.config')

    const modal = $uibModal.open({
        templateUrl: 'ngtmpl/interpretationConfirmation.modal.ngtmpl.html',
        controller: ['canFinalize', '$uibModalInstance', ConfirmCompleteInterpretationController],
        size: 'lg',
        resolve: {
            canFinalize: () => canFinalize(interpretation, alleles, config)
        },
        controllerAs: 'vm'
    })

    return modal.result
        .then((res) => {
            if (res === 'markreview') {
                return path.markreview()
            } else if (res === 'finalize') {
                return path.finalize()
            }
            return path.cancelled()
        })
        .catch(() => {
            return path.cancelled()
        })
}
