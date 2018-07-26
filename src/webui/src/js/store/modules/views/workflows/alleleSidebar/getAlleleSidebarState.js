export default function getAlleleSidebarState() {
    return {
        expanded: true,
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
            }
        }
    }
}
