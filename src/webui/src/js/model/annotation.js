/* jshint esnext: true */

export default class Annotation {
    /**
     * Represents one Annotation
     * @param  {object} Annotation data.
     */
    constructor(data) {
        Object.assign(this, data)
        if (this.filtered_transcripts && this.filtered_transcripts.length) {
            this.filtered = this.transcripts.filter(anno =>
                this.filtered_transcripts.includes(anno.transcript)
            )
        } else {
            this.filtered = this.transcripts
        }
    }

    /**
     * Checks whether the allele has a transcript with worse consequence than
     * the filtered ones. We use the 'worst_consequence' array from backend
     * and match it against our list of filtered transcripts. If there is no overlap,
     * there are other transcripts with worse consequence.
     * @return {Boolean} True if 'worse_consequence' contains transcripts not in 'filtered_transcripts'
     */
    hasWorseConsequence() {
        if (!this.filtered_transcripts) {
            return false
        }
        return !this.worst_consequence.some(n => {
            return this.filtered_transcripts.includes(n)
        })
    }

    getWorseConsequenceTranscripts() {
        return this.worst_consequence.map(name => {
            return this.transcripts.find(t => t.transcript === name)
        })
    }
}
