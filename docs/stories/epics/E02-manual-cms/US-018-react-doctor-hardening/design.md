# Design

Fix React Doctor findings that are actionable and relevant:

- make exported server actions authenticate before reading form data;
- remove module-level mutable-looking server action initial state;
- replace plain internal anchor with `Link`;
- add basic metadata to public pages;
- improve vague login button label;
- simplify trusted origin parsing.

Keep known false positives documented if remaining.
