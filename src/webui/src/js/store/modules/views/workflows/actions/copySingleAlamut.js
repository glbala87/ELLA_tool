import { state } from 'cerebral/tags'
import sortAlleles from '../computed/sortAlleles'

export default function copyAllAlamut({ clipboard, resolve }) {
    let alleles = resolve.value(sortAlleles(state`views.workflows.data.alleles`, false))
    clipboard.copy(alleles.map(a => a.formatted.alamut).join('\n'))
}
