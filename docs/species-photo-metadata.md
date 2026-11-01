# Species photo metadata audit

Audit date: 2026-11-01

## Result

`photos/species.json` contains 4,802 image entries. Fifteen now have a separate, image-specific author, license, license URL where applicable, and exact Wikimedia Commons file page in `photos/species_metadata.json` (0.31%). The other 4,787 remain unchanged and continue to use their existing Wikipedia attribution. Existing image URLs and choices were not changed.

The metadata sidecar preserves the legacy two-item photo tuple. The runtime uses sidecar credits where present; unreviewed candidates remain `legacy` and are not promoted to approved photo candidates. Public-domain entries have no license URL because Commons provides none for those records.

## Method

For each of the 15 additions, the filename was extracted from the existing thumbnail URL and looked up as an exact `File:` title using the Wikimedia Commons Action API `action=query&prop=imageinfo&iiprop=extmetadata`. The stored author comes from the API's `Artist` field, the license and URL from `LicenseShortName` and `LicenseUrl`, and the `p` value links to that exact Commons file page. Only complete records with a non-empty author and explicit license were included; ambiguous or missing values were left out. No article authorship, inferred licenses, or alternate providers were used.

The 15 reviewed titles are: Aardwolf; Abaeis nicippe; Abies; Abies balsamea; Abies concolor; Abies fargesii; Abies fraseri; Abies grandis; Abies magnifica; Abies procera; Abies religiosa; Abies spectabilis; Abronia fragrans; Abrus precatorius; Abutilon grandifolium.

## Unresolved records

Every key in `photos/species.json` absent from `photos/species_metadata.json` is unresolved. Counts below are for the remaining 4,787 entries:

| Existing image URL form | Remaining entries | Notes |
| --- | ---: | --- |
| Relative Commons thumbnail (`330px-` form) | 4,712 | The same basic source form as the first verified batch; must still be checked file by file. |
| Direct `upload.wikimedia.org` Commons file URL | 67 | Exact file identity is available, but author and license have not been audited yet. |
| Absolute `thumb.wikimedia.org/wikipedia/en/` thumbnail | 4 | Wikipedia-hosted source; Commons identity and corresponding license must not be inferred. |
| Transformed relative TIFF thumbnail (`lossy-page1-330px-`) | 4 | The thumbnail name is transformed; original file title needs exact resolution before API lookup. |
| **Total unresolved** | **4,787** | No metadata was guessed or copied from the article. |

Across all 4,802 entries, the source-form totals are 4,727 relative Commons thumbnails, 67 direct Commons upload URLs, 4 absolute Wikipedia-hosted thumbnails, and 4 transformed relative TIFF thumbnails. There are 4,760 distinct normalized filenames; 35 filenames are reused by multiple manifest keys, so subsequent batches should avoid repeating API work while still attaching verified metadata to each exact image entry.

## Next batch

Continue in batches of about 15 exact Commons files. Resolve duplicate filenames once per batch, but check each manifest key's file URL before attaching shared source metadata. Keep the four Wikipedia-hosted and four transformed TIFF records out of the Commons batch until their exact original file identities can be established.
