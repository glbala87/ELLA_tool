/* jshint esnext: true */

export class Annotation {
    /**
     * Represents one Annotation
     * @param  {object} Annotation data.
     */
    constructor(data) {
        Object.assign(this, data);
        this.setFilteredTranscripts();
    }

    /**
     * Set 'filtered' property based on key from 'filtered_transcripts'
     * and data from 'transcripts'
     */
    setFilteredTranscripts() {
        this.filtered = this.annotations.transcripts.filter(t => {
            return this.annotations.filtered_transcripts.includes(t.Transcript);
        });
    }
}
