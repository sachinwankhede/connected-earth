# Node names: the row name decides (22 Nov, #1061)

Before any node `name` override is dropped (I2) the row must carry the right name, because the page shows the row name.

## The rule (owner agreed 22 Nov)

**A row's name is the English Wikipedia title of its page.** A row already maps to exactly one article (I1), and the title is the common name Wikipedia settled on. When the title is only the scientific name, the English label of the article's Wikidata item stands in, with a capital first letter. A page that is missing, a disambiguation page, or has no English label cannot be settled by the rule: the owner names those by hand.

The first draft of this document proposed "the name most nodes use". That was withdrawn: read row by row, about half the proposals were worse than today's name (Abyssus for the Western rattlesnake, "Moose (alces)", Weymouth Pine, Sage-of-the-desert for Saguaro, "California/Woodhouse's Scrub-Jay"), because nodes carry place-local names, which is what the row name must not follow (#1038).

## How it is applied

1. `jobs/rowtitles.py` (read-only; workflow `readonly-rowtitles`, owner-merged because it is under `.github/`) lists the rows a node still names differently with the proposed name and where it came from, the rows that already match, and the rows that cannot be settled. It writes nothing.
2. The owner reads the "would change" and "cannot be settled" lists.
3. A data pull request (by hand, allowed for this cleanup) renames the rows the owner keeps. The proposal is a row rename only: ids, pages and pictures do not change.
4. Node `name` overrides on those rows are then dropped in batches, with the name cap in `build/validate_data.py` lowered with each batch.

## Group rows

Their names stay. The local wording a node had ("Puna bunchgrasses", "Reef algae") moves into the node's `desc` so nothing is lost. The decomposers row (154 nodes) gets a plain group name.

## Not yet decided

- Resource nodes whose names `species.py pack` still reads (#1088) keep their names until `pack` takes the species from `sp`.
- 83 nodes whose name shares no specific word with their row (for example "Jackalberry" on African ebony) are probably the wrong species and are repointed or given their own row by the update process, not renamed.
