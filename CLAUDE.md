# Connected Earth

- Before any UI work, read `docs/DESIGN.md` and follow it. If a request conflicts with a rule, point it out and update the rule rather than quietly breaking it.
- Build with `python3 build/build.py --all` (never hand-edit index.html or sw.js). Test only the affected area while iterating; the full suite runs in CI before merging to main.
- Merging to main and deleting branches or previews is the owner's call; ask first.
