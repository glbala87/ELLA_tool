export default function showAlleleAssessmentHistoryModal({
    AlleleAssessmentHistoryModal,
    props,
    path
}) {
    const { alleleId } = props
    return AlleleAssessmentHistoryModal.show(alleleId)
        .then(result => {
            if (result) {
                return path.result()
            }
            return path.dismissed()
        })
        .catch(result => {
            return path.dismissed()
        })
}
