# riskell-registry

The index of extensions for [riskell](https://github.com/rish139/riskell). A listing is a small JSON file that points at an author's own
repository at one pinned commit: nothing is hosted here, no agreement is needed, and the code stays under its author's license.

- **Find and install:** `risk ext search <words>`, `risk ext info <name>`, `risk ext add <name>`, `risk ext update`. Or browse the storefront (generated
  from this repository, one static page).
- **List yours:** in your extension's repository run `risk ext publish`: it checks the repository is ready and prints the listing. Save it as
  `listings/<id>.json` and open a pull request. CI checks the fields and the repository at that commit (the manifest agrees, the validator passes).
  An update is a new pull request with the new commit; people get it with `risk ext update`, which shows the change first.

A listing needs: `id`, `kind` (`atom`, `reading`, `pill`, `theme`), `name`, `summary` (140 characters), `repo` (https), `rev` (the full commit),
`version` (equal to your `riskell.json`, with a tag `v<version>` on that commit), `license`, and a `preview`: a PNG in your repository (at least 600 px wide, up to 500 KB) showing the widget, which the storefront displays. `risk ext publish` asks for it; riskell can render one with `riskell --snap`. See `schema/listing.schema.json`.

`scripts/check-listing.py` (the checks), `scripts/build-index.py` (`index.json`) and `scripts/build-site.py` (the page) need only Python 3.
Listings marked `bundled` are the ones that ship with riskell itself.

Preview the storefront with made-up samples: `python3 scripts/build-site.py --sample`, then open `site-preview/index.html`.
