## Background

Prepare and release [version]

--- DELETE ME ---

Remember:

- Assign **Weight**, if possible

--- DELETE ME ---

## Tasks specific for this release

[List tasks that are specific for this release here]

## Tasks that should always be performed

### Staging, before user verification test
- [ ] Automatic import (specific samples and detailed check list)
- [ ] Manual import (specific samples and detailed check list)
- [ ] Exports (EKG, all variants)
- [ ] CLI: check fixtures, usergroups, gene panels, filter configs
- [ ] Load test (automated script; Hey)

### On startup of ELLA
- [ ] Schema checks
- [ ] Check filter config

### Post release
- [ ] Check logs that all processes are running without errors

## Testing and documentation
- [ ] Release notes (list any breaking changes)

### Feature changes?
- [ ] ELLA endringskontroll (versjonsoppdatering)
- [ ] Verifiseringstest: New or changed functionality (before production, in staging env)
- [ ] Akseptansetest: In production env, before full release. Standardized check list
- [ ] Not applicable (bugfix release)

### Major changes? (import/filter) 
- [ ] Risk evaluation
- [ ] Verifiserings-/valideringsrapport
- [ ] Not applicable

/label ~"work::draft" ~"type::chore" ~"DMG docs"
/confidential 