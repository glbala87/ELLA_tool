import copyGenesToClipboard from '../actions/copyGenesToClipboard'
import toast from '../../../../../../common/factories/toast'

export default [copyGenesToClipboard, toast('info', 'Copied genes to clipboard')]
