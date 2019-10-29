import { props, string } from 'cerebral/tags'
import { redirect } from '../../../../common/factories/route'

export default [redirect(string`/overview/${props`section`}`)]
