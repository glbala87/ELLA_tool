import { props, string } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'

export default [redirect(string`/overview/${props`section`}`)]
