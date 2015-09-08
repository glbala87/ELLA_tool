/* jshint esnext: true */

class Annotation {
    /**
     * Represents one Annotation
     * @param  {object} Annotation data.
     */
    constructor(data) {
        Object.assign(this, data);
        this.filtered = [];  // Filtered transcripts
    }

    _unversionTranscript(name) {
        return name.split('.')[0];
    }

    /**
     * Filters annotation's transcript data according to provided
     * input.
     * @param  {Transcript} transcripts Array of Transcripts (e.g. from genepanel) or single Transcript.
     * @return {[object]} List of matching data objects.
     */
    setFilteredTranscripts(transcripts) {
        if (!Array.isArray(transcripts)) {
            transcripts = [transcripts];
        }

        let filtered = [];

        let filterTranscriptGene = (t, g) => {
            return this.annotations.transcripts.find(el => {
                // We don't filter on version of the transcript.
                return el.Transcript === this._unversionTranscript(t) &&
                       el.SYMBOL === g;
            });
        };

        for (let t of transcripts) {
            let transcript_data = filterTranscriptGene(t.refseqName, t.gene.hugoSymbol);
            if (transcript_data) {
                filtered.push(transcript_data);
            }
        }
        this.filtered = filtered;

    }
}
