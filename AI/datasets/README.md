# Hugging Face dataset observations

Executable Python standard-library integration for DeepCore's advisory AI
layer. Uses the existing `CORE.deepcore_runtime` canonical serialization and
SHA-256 helpers. Dataset text is untrusted input, never an instruction or an
authorized financial transaction. No remote Python dataset scripts run.

## Included data

Source: [zeroshot/twitter-financial-news-sentiment](https://huggingface.co/datasets/zeroshot/twitter-financial-news-sentiment).
The publisher's card states MIT licensing. Attribution and source metadata
remain with each observation; downstream users must retain applicable notices.
Pinned revision: `ccbe24de388e287beb92dd393a335c376b350ac3`.

| Registry name | Source file | Purpose |
| --- | --- | --- |
| financial-news-train | sent_train.csv | Training or development |
| financial-news-validation | sent_valid.csv | Held-out sentiment evaluation |

Labels: 0 bearish, 1 bullish, 2 neutral. Keep validation records out of training.
The pinned files contain 9,543 training and 2,388 validation records when
parsed (11,931 total); these observed counts differ from the dataset card.
These historical English-language tweets can test sentiment classification;
they are not live prices, wallet ownership evidence, trading signals, mining
telemetry, or a measure of cryptographic correctness. The repository currently
has no trained sentiment classifier; importing this corpus does not train one.

## Run from repository root

```bash
mkdir -p /tmp/deepcore-datasets
python -m AI.datasets.ingest financial-news-train --database /tmp/deepcore-datasets/observations.sqlite
python -m AI.datasets.ingest financial-news-validation --database /tmp/deepcore-datasets/observations.sqlite
python -m pytest -q tests/test_huggingface_datasets.py tests/test_deepcore_runtime.py
```

For durable use choose a dedicated persistent volume outside the checkout.
The parent directory must exist. Do not use a financial ledger database.
Imports download public CSV files without credentials, check the pinned file
hash and validate the complete CSV before a single SQLite transaction inserts
rows. Failed imports exit nonzero; reruns skip identical records and reject
conflicting stored content. Limits: 16 MiB per source, 100,000 rows, 30-second
socket timeout. Network failures can be retried by rerunning the command.
No GPU, paid job, background service, or automatic download at startup is used.

## Consume observations

```python
from AI.datasets.ingest import read_observations

for record in read_observations('/tmp/deepcore-datasets/observations.sqlite'):
    row = record['body']
    if row['split'] == 'validation':
        text, expected_label = row['text'], row['label']
        # Pass text as data to your advisory evaluator.
```

Each record carries source repository, revision, file checksum, split, row
index, purpose, license, and a deterministic observation ID. Readback checks
the record hash. This detects accidental alteration; it is not authentication
against an attacker who can replace the database and recompute hashes.
There is no Kafka publishing or consensus/ledger write path in this adapter.

To add a dataset, review its source, license, task relevance and schema; pin
its commit and file SHA-256 in `registry.json`, and add a tested adapter if it
is not a `text,label` CSV. Do not add unrelated corpora just to increase size.
CI uses synthetic fixtures offline; actual source downloads are separate
integration checks. Imported records and databases must not be committed.

## Verification evidence (2026-09-16)

- 11 dataset tests passed using Python 3.12 and pytest 8.4.2.
- Live HTTPS imports passed both pinned source checksums and imported 11,931 rows.
- Reimporting validation inserted 0 records and skipped 2,388 duplicates.
- Existing runtime suite: 10 passed, 1 failed in `test_weighted_quorum`.
  The existing test expects false for weight 5/7 although the implementation
  returns true for the two-thirds weight threshold. Neither file was modified.
- No production deployment or model training was performed.
