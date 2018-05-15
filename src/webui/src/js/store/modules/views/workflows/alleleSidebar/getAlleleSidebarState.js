export default function getAlleleSidebarState() {
    return {
        unclassified: null,
        classified: null,
        orderBy: {
            unclassified: {
                key: null,
                reverse: false
            },
            classified: {
                key: null,
                reverse: false
            }
        }
    }
}
