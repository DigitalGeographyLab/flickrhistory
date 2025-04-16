- **0.3.1** (2025-04-16):
    - fix race conditions around tags (duplicate keys)

- **0.3.0** (2025-04-15):
    - now collecting more data: tags, license, geo-accuracy
    - re-downloading these data for existing records
    - database schema versioning
    - moved to PyPi TrustedPublisher auth
    - migrated to pyproject.toml-only style

- **0.2.1** (2024-01-08):
    - migrate to Digital Geography Lab’s GitHub

- **0.2.0** (2023-02-13):
    - server-side cursors for catching up missed data records

- **0.1.4** (2023-02-01):
    - fixed bug introduced in 0.1.3

- **0.1.3** (2023-01-31):
    - handle connection errors more gracefully (issue #20)

- **0.1.2** (2023-01-30):
    - fix a bug that caused `date_taken` to not be recorded (issue #19)

- **0.1.1** (2022-05-20):
    - obtain Zenodo DOI
    - push to PyPi

- **0.1.0** (2022-03-30):
    - stop looping after all data until start timestamp retrieved

- **0.0.9** (2020-10-11):
    - added README (issue #7)
    - fixed issue with database connections being left open (issue #15)
    - worked around incomplete API responses (issue #9)
    - dumped dunamai (for good?)


- **0.0.8** (2020-11-09):
    - improvement: multi-threaded user profile download (re issue #8)
    - removed dunamai, run it as a git pre-commit hook, rather


- **0.0.7** (2020-11-09):
    - fixed issue #6: working around bogus API responses,
    - one more try with dunamai for automatic semantic versioning


- **0.0.6** (2020-11-07):
    - fancy console output 💍


- **0.0.5** (2020-11-07):
    - fixed issue #2 (improvement): use deque instead of queue for todo list


- **0.0.4** (2020-11-07):
    - fixed issue #1: flickr API returning 0 instead of “too many”


- **0.0.3** (2020-11-07):
    - Work around race conditions due to poor SQLAlchemy BEGIN/COMMIT/UPSERT handling
    - Discard photos outside download time window early


- **0.0.2** (2020-11-06):
    - Get rid of dunamai


- **0.0.1** (2020-11-06):
    - First functional release
