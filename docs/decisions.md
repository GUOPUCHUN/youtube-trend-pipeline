\# Architecture Decision Records



\## ADR-001: Upstream data source semantics changed mid-project



\### Context

The project was scoped around "YouTube trending videos" via

`videos.list?chart=mostPopular`.



\### Finding

Per Google's changelog, as of 2025-07-21 the `mostPopular` chart no longer

reflects the "Trending Now" list. It now surfaces videos from the Trending

Music / Movies / Gaming charts, alongside the deprecation of YouTube's

Trending page.



Verified empirically (regionCode=JP, maxResults=10): the observed

`categoryId` distribution was {10 Music, 24 Entertainment, 20 Gaming,

1 Film \& Animation}.

Note that categoryId 24 (Entertainment) is \*\*not\*\* mentioned in the

changelog. Actual behaviour is broader than documented. Sample size is small

(n=10, single region, single day), so this is recorded as an observation

rather than a claim.



\### Decision

\- Keep the data source; the pipeline mechanics are unaffected.

\- Describe the dataset in the README as the "mostPopular chart", never as

&#x20; "trending videos".

\- Treat upstream documentation as unreliable. Validate response structure

&#x20; explicitly rather than trusting field presence.



\### Consequence

This is the concrete justification for fail-fast schema validation: the

upstream contract already changed once within the project's lifetime, and

the official description of that change was incomplete.



\---



\## ADR-002: Hand-written ISO 8601 parser instead of a library



\### Context

`contentDetails.duration` arrives as an ISO 8601 string (`PT4M13S`).

Analysis needs an integer number of seconds.



\### Decision

Parse with a purpose-built regex rather than adding `isodate`.



\### Rationale

\- The input domain is constrained to what YouTube actually returns

&#x20; (`PT\[nH]\[nM]\[nS]`); the full ISO 8601 grammar is not needed.

\- Twenty lines with complete test coverage is a smaller liability than an

&#x20; additional dependency in the Lambda package.



\### Consequence

Parse failures raise `DurationParseError` rather than returning `0`.

Returning a default would let malformed records flow silently into

aggregate statistics, producing wrong answers with no signal.



If requirements expand to full ISO 8601 (e.g. `P1Y2M3D`), this decision

should be revisited in favour of a library.



\---



\## ADR-003: pyarrow directly, not pandas



\### Context

The curated zone stores Parquet. The obvious path is

`pandas.DataFrame.to\_parquet()`.



\### Decision

Write Parquet with `pyarrow` directly, using an explicit schema.



\### Rationale

\- pandas plus pyarrow exceeds Lambda's unzipped size budget comfortably;

&#x20; pyarrow alone fits without needing a managed layer.

\- An explicit `pa.schema` keeps column types stable across daily partitions.

&#x20; Type inference would let a day of all-null `like\_count` values change that

&#x20; column's type, breaking the Glue table.



\### Consequence

Adding a column requires updating the schema in two places (the flattener

and the Parquet schema). This is accepted as the cost of type stability.



\---



\## ADR-004: Partition projection instead of a Glue crawler



\### Context

Athena needs to know which partitions exist under `curated/`.



\### Decision

Use Glue partition projection (`projection.enabled = true`) rather than

running a crawler or issuing `ALTER TABLE ADD PARTITION`.



\### Rationale

\- Partitions follow a fully predictable daily pattern, which is exactly the

&#x20; case projection is designed for.

\- No crawler schedule to run, no crawler cost, no window in which a written

&#x20; partition is not yet queryable.

\- Idempotent by construction: re-running a day overwrites the object and

&#x20; requires no catalog change at all.



\### Consequence

The projection range (`2026-08-01,NOW`) is configuration that must be kept

in step with the actual data range.

