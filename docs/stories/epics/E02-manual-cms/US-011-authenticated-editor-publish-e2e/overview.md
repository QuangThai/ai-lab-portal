# Overview

## Current Behavior

US-009 proves authenticated admins can open the editor. US-008 wires server actions, but E2E does not yet click save/publish and observe the result.

## Target Behavior

Authenticated E2E proves the editor can submit content through Next.js server actions to the FastAPI admin API without exposing admin boundary secrets to browser code.

## Non-Goals

- No AI workflow.
- No media upload.
- No production auth bypass.
