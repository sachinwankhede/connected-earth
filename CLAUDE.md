# Connected Earth

- Before any UI work, read `docs/DESIGN.md` and follow it. If a request conflicts with a rule, point it out and update the rule rather than quietly breaking it.
- Build with `python3 build/build.py --all` (index.html, pilot/index.html, sw.js and webs/ are built by CI and the deploy and are not committed; never hand-edit them). Test only the affected area while iterating; the full suite runs in CI before merging to main.
- Merging to main and deleting branches or previews is the owner's call; ask first.
