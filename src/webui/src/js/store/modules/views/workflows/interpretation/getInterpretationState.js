export default function getInterpretationState() {
    return {
        selectedId: null, // id or "current"
        isOngoing: false,
        dirty: false, // Whether state is dirty (not saved)
        state: null,
        userState: null,
        geneInformation: {
            geneassessment: {}
        },
        data: {
            filteredAlleleIds: null, // {allele_ids: [], excluded_alleles_by_caller_type: {}}
            filterConfig: null,
            alleles: null,
            genepanel: null,
            attachments: null,
            references: null
        }
    }
}
