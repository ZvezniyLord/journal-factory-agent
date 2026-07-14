---
name: naukainfo-figure-cluster-fidelity
description: Treats each figure, embedded caption/textbox, external caption, and source note as an atomic ordered cluster and prevents loss or detachment.
version: "2.9.0"
---
# Atomic figure cluster

Protected order signature:
`preceding prose → figure object → caption → source note → required blank → following prose`.

Audit both main body and nested `w:txbxContent`. Every drawing/picture/object paragraph uses the template figure-object style `РИС` (`styleId ad`). Every recognized caption (`Рис.`, `Мал.`, `Fig.`, `Figure`, `Abb.`, `Abbildung`, `AGD1`, etc.) uses `РисПід` (`styleId af6`), single spacing, centered, zero first-line indent.

A caption embedded inside a shape is still a caption. A composite raster containing several subfigures is one author object unless the source contains separate editable objects.

Release fails if a source object is absent, reordered, detached from its caption, clipped, outside printable margins, or replaced by a different image hash.
