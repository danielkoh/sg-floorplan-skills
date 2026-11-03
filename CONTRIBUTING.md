# Contributing

Thank you for helping. Pull requests of any size are welcome, and so are issues that point out a
mistake. This project is early and not perfect; the rules below exist so that what it says stays
checkable.

## The rules that keep it honest

1. **Renovation rules need a primary source.** A new or changed rule in
   `skills/sg-reno-rules/rules.yaml` carries the verbatim quote, the URL (SCDF, URA, BCA, EMA,
   Singapore Statutes Online, or another government source), the page's own updated date and the
   date you fetched it. A media, law-firm or retailer source can only make a rule `unverified`.
2. **Sizes and clearances carry a source and a grade** in `standards.yaml`.
3. **Positive, household-first wording.** Describe what a layout gives a household and who it
   suits. No "problem", "issue", "flaw" or "waste", and no criticism of a developer or a project.
4. **No real people or private details.** No owners' names, unit numbers tied to a person,
   addresses, or anything copied from material marked internal or not for circulation. No
   developer plan images in the repo; tests use synthetic plans.
5. **Tests pass.** Run `python3 -m pytest -q` and `python3 skills/sg-reno-rules/verify.py`.
   Add a test when you add a trait, a check or a rule.

## How

Fork, branch, change, run the tests, open a pull request saying what changed and where the
source is. If you're unsure whether something fits, open an issue first; that's fine too.
