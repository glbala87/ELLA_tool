import sortAlleles from '../computed/sortAlleles'

export default function copyAllAlamut({ state, clipboard, resolve }) {
    let alleles = resolve.value(
        sortAlleles(Object.values(state.get('views.workflows.interpretation.data.alleles')))
    )
    clipboard.copy(alleles.map((a) => a.formatted.alamut).join('\n'))
}
