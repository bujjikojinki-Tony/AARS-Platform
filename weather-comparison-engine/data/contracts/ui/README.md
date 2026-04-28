# UI Contract Schemas

This directory contains draft JSON Schema files for governed UI view contracts.

These schemas are intentionally lightweight in the first landing pass. They define:

- required contract identity fields
- top-level page object structure
- entry context shape for cross-page navigation
- basic operator/UI action event shape for cross-page audit and replay

They do not yet attempt to exhaustively validate every nested field used by every
surface. That deeper validation can be added incrementally as the view builder
layer stabilizes.
