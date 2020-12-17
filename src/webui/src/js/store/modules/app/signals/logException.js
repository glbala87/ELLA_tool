import toast from '../../../common/factories/toast'
import postException from '../actions/postException'

export default [
    postException,
    toast(
        'error',
        'An error occured. Please save your work and reload the page. If the problem persists, please contact support',
        100000000
    )
]
