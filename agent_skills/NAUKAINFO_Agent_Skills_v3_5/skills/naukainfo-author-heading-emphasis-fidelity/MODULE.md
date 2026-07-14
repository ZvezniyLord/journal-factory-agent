---
name: naukainfo-author-heading-emphasis-fidelity
description: Preserves author-created body emphasis for section labels such as Introduction, Materials and methods, Results, Conclusions while allowing only journal style assignments that do not remove bold/italic semantics.
version: "2.8.0"
---

# Rule

Body subheadings written by the author, for example `Вступ`, `Матеріали та методи`, `Результати та їх обговорення`, `Висновки`, `Introduction`, `Materials and methods`, `Results`, `Conclusions`, are part of the article body.

If the author made them bold, centered, italic, or otherwise emphasized, that emphasis must remain after normalization and journal insertion.

# Regression lesson

In the Magdysiuk article, body subheadings stayed centered but lost bold. This is a content-fidelity regression, not a cosmetic issue.

# Validation

Compare source and final for each recognized body subheading:

- text exactness;
- paragraph order;
- alignment;
- bold/italic/all-caps emphasis;
- spacing.

Do not convert these body subheadings into TOC headings unless the business plan explicitly says so.
