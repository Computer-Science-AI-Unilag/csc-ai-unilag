# Contributing to CSC AI UNILAG

Thank you for improving this archive. Contributions are reviewed before publication; submitting a pull request does not make a resource an official course document.

## Before you begin

Read the [Code of Conduct](CODE_OF_CONDUCT.md). Do not add private contact details, student records, unapproved recordings, copyrighted material without permission, or secrets.

## Contribution workflow

1. Open an issue or choose an existing documentation task.
2. Fork the repository or create a descriptive branch such as `docs/week-01-notes`.
3. Find the correct academic session, course, module, and week under `years/`.
4. Edit Markdown with clear headings and working relative links. Use `templates/` for new material.
5. Add notebooks only beside the relevant lecture; clear outputs and remove credentials.
6. Run `python scripts/validate_structure.py`.
7. Commit with a clear message, for example `docs: add approved Week 03 notes`.
8. Open a pull request using the repository template. A maintainer reviews accuracy, permissions, and structure.

## Adding or correcting materials

- Add lecture notes only with the source owner's permission.
- Add a YouTube URL only after it is published and approved.
- Report uncertain information in an issue rather than guessing.
- State the academic year and course affected in every pull request.
- Use meaningful names such as `notes.md`, `assignment.md`, or `lab-search-basics.ipynb`.

## Local checks

```powershell
python scripts/validate_structure.py
```

The checker validates core files, structure, weekly metadata, and local Markdown links. It cannot establish lecturer approval or test external URLs.

## Reviews and authorship

By contributing, you confirm that your work is original or you have permission and attribution. Maintainers may request revisions or decline inaccurate or inappropriate material.
