# SKILL_INTEGRATION.md
## Accepted skill exchange decisions for Astra

The Jurnal_Skills -> NAukaInfo exchange has been resolved for this clean-room Astra project.

## Decisions

| Capability | Decision | Astra integration |
|---|---|---|
| DOCX/OOXML forensic audit | ACCEPT | structural/package validators |
| Word bibliography numbering / REFER | ACCEPT | reference engine + golden tests |
| Source -> final integrity audit | ACCEPT | content/formatting/object QA |
| Word/render visual QA | ACCEPT | release QA |
| People roles metadata separation | ADAPT | supplement existing header rules only |
| Front matter immutability | ACCEPT | front-matter guard |
| TOC <-> body consistency | ACCEPT | TOC builder/validator |
| Clean-room path guard | ACCEPT | workspace boundary |
| Hermes semantic delegation | ACCEPT | mandatory local subagent |
| Journal release gates | ACCEPT | fail-closed release layer |

## Existing NAukaInfo capabilities that stay authoritative

Do not replace:
- existing UDC capability/workflow;
- existing spelling/header capability/workflow.

For people-role metadata, borrow only:
- separate authors / supervisors / affiliations / positions;
- supervisor is not automatically a coauthor;
- supervisor appears in TOC for NAukaInfo profile.

## Implementation rule

Do not build ten unrelated "skills" or autonomous agents.

Translate accepted knowledge into:
- typed schemas;
- config;
- deterministic modules;
- Hermes task schemas;
- validators;
- golden/regression tests;
- release gates.

The only model subagent in this architecture is local Hermes, used for bounded semantic tasks. Astra remains orchestration and mutation authority.
