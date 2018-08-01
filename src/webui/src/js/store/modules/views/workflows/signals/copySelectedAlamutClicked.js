import toast from '../../../../common/factories/toast'
import copySelectedAlamut from '../actions/copySelectedAlamut'

export default [copySelectedAlamut, toast('info', `Copied selected variant to clipboard`)]
