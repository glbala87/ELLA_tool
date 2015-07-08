/* jshint esnext: true */

class Annotation {
    /**
     * Represents one Annotation
     * @param  {object} Annotation data.
     */
    constructor(data) {
        Object.assign(this, data);
    }

    /**
     * Filters annotation's transcript data according to provided
     * input.
     * @param  {Transcript} transcripts Array of Transcripts or single Transcript
     * @return {[object]} List of matching data objects.
     */
    filterTranscripts(transcripts) {
        if (!Array.isArray(transcripts)) {
            transcripts = [transcripts];
        }

        let filtered = {};

        let getTranscriptData = (t) => {
            return this.annotations.transcripts[t.refseqName];
        };

        for (let t of transcripts) {
            if (t.refseqName in this.annotations.transcripts &&
                t.gene.hugoSymbol == getTranscriptData(t).CSQ.SYMBOL) {
                filtered[t.refseqName] = getTranscriptData(t);
            }
        }
        return filtered;

    }
}
