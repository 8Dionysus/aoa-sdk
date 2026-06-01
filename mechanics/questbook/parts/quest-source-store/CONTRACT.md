# Quest Source Store Contract

## Contract

Source quest records live at `quests/<lane>/<state>/<quest-file>`.

## Must

- keep stable quest IDs unless a decision records the rename;
- choose a lane before choosing a state;
- keep helper authority with the owning mechanic part;
- keep public obligation visibility in `QUESTBOOK.md`.

## Must Not

- hide active quest source records in `mechanics/<parent>/parts/<part>/quests/`;
- use quest notes as proof verdicts, owner acceptance, release readiness, or
  runtime activation;
- add top-level quest aliases.
