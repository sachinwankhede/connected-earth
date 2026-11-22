# Node names: the row name decides (22 Nov, #1061)

Before any node `name` override is dropped (I2) the row must carry the right name, because the page shows the row name.

## The rule (owner agreed 22 Nov; decision order added 22 Nov at the owner's request)

**A row is one concept with one Wikipedia page (I1), and its name is that concept's English name.** The owner does not rule row by row; the name is taken from the data in this order, and the first step that gives an answer decides:

1. The page title, when it is a common name (Wikipedia has settled it).
2. The English label of the page's Wikidata item, when the title is only the scientific name, with a capital first letter.
3. The English common names Wikidata lists for the taxon (property P1843): the row keeps its current name when that name is on the list, otherwise it takes the first listed.
4. A row whose current name is **more specific than its page** ("Feral cat" on the page of the domestic cat) is a different concept from that page. If the specific name is itself a Wikipedia article, the concept is its own row (own page, own picture and summary), and the nodes that mean it are repointed to it (a place update). If it is not an article, the name is local wording: the row takes the page's name and the wording moves to the node `desc`. A row whose page is not the species its name and nodes describe (Wild horse on the page "Mustang") is repointed to the right page.
5. A page that is missing, a disambiguation page, or has no name from steps 1 to 3 is the only case left for the owner.

Group rows follow step 1 with the singular group name the page uses (Moths becomes Moth); their local wording goes to the node `desc`.

The first draft of this document proposed "the name most nodes use". That was withdrawn: read row by row, about half the proposals were worse than today's name (Abyssus for the Western rattlesnake, "Moose (alces)", Weymouth Pine, Sage-of-the-desert for Saguaro, "California/Woodhouse's Scrub-Jay"), because nodes carry place-local names, which is what the row name must not follow (#1038).

## How it is applied

1. `jobs/rowtitles.py` (read-only; workflow `readonly-rowtitles`, owner-merged because it is under `.github/`) applies steps 1 to 4 (read-only; for step 4 it reports an own article but does not yet check that the article has a licensed picture, which the add process requires) and prints, for each row a node still names differently, the proposed name and the step that gave it, the rows that already match, and the rows left for the owner.
2. A data pull request (by hand, allowed for this cleanup) applies the renames and repoints the job proposes; a new row goes through the add process (licensed picture required, refusal ledger).
3. Node `name` overrides on those rows are then dropped in batches, with the name cap in `build/validate_data.py` lowered with each batch.

## Group rows (local wording)

The local wording a node had ("Puna bunchgrasses", "Reef algae") moves into the node's `desc` so nothing is lost. The decomposers row (154 nodes) gets a plain group name.

## Not yet decided

- `species.py pack` now takes a node's row from `sp` (#1094, closing #1088), so resource-node names can be dropped.
- 83 nodes whose name shares no specific word with their row (for example "Jackalberry" on African ebony) are probably the wrong species and are repointed or given their own row by the update process, not renamed.
