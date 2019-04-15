export default function getInterpretationState() {
    return {
        selectedId: null, // id or "current"
        isOngoing: false,
        dirty: false, // Whether state is dirty (not saved)
        state: null,
        userState: null,
        data: {
            filteredAlleleIds: null, // {allele_ids: [], excluded_allele_ids: {}}
            filterConfig: null,
            alleles: null,
            genepanel: null,
            attachments: null,
            references: null
        }
    }
}
