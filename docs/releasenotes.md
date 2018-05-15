# Release notes

## 1.1

### Highlights

#### New import functionality

*Requires access to the import view.*

ella now lets you re-import previously run samples, using either an existing genepanel or a genepanel customised for that specific sample.

This lets you request new analyses directly in the application and shortens the time for reanalysis with a different set of genes.

<div style="text-align: center"><img style="width: 20rem" src="img/releasenotes/1-1-import.png"></div>


#### Frontend code improvements

The frontend code has been refactored to make it more responsive and to make it easier to add new functionality going forward.


### Other additions and fixes

- Display number of excluded references on 'SHOW EXCLUDED' button
- Remove scrollbar on comment fields.
- When there are multiple transcripts in a genepanel, sort them by name. Also display all transcripts in more places, for example in the variants overview.
- Do not add references with Relevance: 'No' to the excluded references list.
- The 'ADD EXCLUDED' window for adding excluded variants now loads faster.
- Search results will now show correctly when typing quickly.
- Many other smaller UI fixes
