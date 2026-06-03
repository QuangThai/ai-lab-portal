# Design

Use lightweight React/Next form status instead of a toast dependency:

- reusable client submit button with `useFormStatus()`;
- editor action status remains visible in a calm status panel;
- admin list row buttons show pending text and disabled state while submitting;
- keep actions server-side and authenticated.
