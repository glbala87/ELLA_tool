export default function getAlleleSidebarState() {
    return {
        expanded: false,
        unclassified: null,
        classified: null,
        technical: null,
        orderBy: {
            unclassified: {
                key: null,
                reverse: false
            },
            classified: {
                key: null,
                reverse: false
            },
            technical: {
                key: null,
                reverse: false
            },
            notRelevant: {
                key: null,
                reverse: false
            }
        }
    }
}
