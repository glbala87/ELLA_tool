const TITLE = {
    external: 'ADD EXTERNAL DB DATA',
    prediction: 'ADD PREDICTION DATA',
    references: 'ADD STUDIES'
}

const PLACEHOLDER = {
    external: 'CHOOSE DATABASE',
    prediction: 'CHOOSE PREDICTION TYPE',
    references: '-'
}

export default function showCustomAnnotationModal({ CustomAnnotationModal, props, state, path }) {
    const category = props.category
    const title = TITLE[category]
    const placeholder = PLACEHOLDER[category]
    const allele = state.get(`views.workflows.data.alleles.${props.alleleId}`)
    console.log(allele)
    return CustomAnnotationModal.show(title, placeholder, allele, category).then((result) => {
        if (result) {
            return path.result({ customAnnotationData: result })
        }
        return path.dismissed()
    })
}
