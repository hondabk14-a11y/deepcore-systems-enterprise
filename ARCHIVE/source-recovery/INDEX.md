# Source Restoration Index

- `ARCHIVE/zips/` preserves binary package provenance.
- `ARCHIVE/source-recovery/` is reserved for unpacked historical source.
- `src/` remains the reviewed canonical implementation area.
- `tests/` contains executable security and contract tests.
- `docs/` contains architecture and evidence documentation.

Historical package contents are not merged automatically because multiple archives contain competing versions of the same modules. Blindly combining them would be a delightful way to manufacture a security regression.
