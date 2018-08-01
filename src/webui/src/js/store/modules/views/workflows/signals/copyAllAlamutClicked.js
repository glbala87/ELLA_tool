import toast from '../../../../common/factories/toast'
import copyAllAlamut from '../actions/copyAllAlamut'

export default [copyAllAlamut, toast('info', `Copied all variants to clipboard`)]
