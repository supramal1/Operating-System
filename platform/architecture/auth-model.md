# CO Agent Platform — Auth Model

**Status: slice 2, designed not built.**
Slice 1 (single user, single agent) implements the bare plumbing (Google OIDC, Obot credential vault, audit log) but enforces only one identity. This document describes the 40-person target so the slice-1 build does not foreclose it.

The test that slice 1 was built right: adding a second user or agent is a **registration + access-scope entry**, not an auth redesign.

---

## Identity

| Layer | Slice 1 (now) | Slice 2 (target) |
|---|---|---|
| Identity provider | Google OIDC | Google OIDC |
| Tenant | Personal Gmail | `charlieoscar.com` Workspace |
| Allowed users | `malik.roberts@gmail.com` (one) | All `@charlieoscar.com` staff (~40) |
| User store | Obot email allowlist (single entry) | Obot reading group claims from Google Workspace |
| Federation | None | TBD at CO onboarding — is there a WPP SSO layer in front of CO Workspace? Open question. |

**Swap path slice 1 → slice 2:** new OAuth client ID + secret in CO Google Cloud project, replace `OBOT_SERVER_AUTH_OWNER_EMAILS`, swap callback URL. No application code change.

---

## Authorisation — designed only

The slice-2 access model authorises users by **role mapped to teams/clients**, not by individual ACL. The three principles:

1. **Authenticate via CO's IdP**, not a separate Obot user list. Obot is a relying party on Google Workspace, never a primary identity store.
2. **Authorise by role**, where role = membership in a Google Workspace group. Roles map to teams (e.g., `co-innovation`, `co-data`) and to clients (e.g., `client-pepsi`, `client-coke`).
3. **Enforce client isolation at the gateway.** An agent invoked by Client A's team must not be able to reach Client B's data or credentials.

The mechanism Obot offers for #2 and #3 is the **MCP Registry**: named buckets of MCP servers, attached to user groups. One registry per client → that client's team sees only their agents and only their credentials.

```
Google Workspace group → Obot user role → Obot MCP registry → reachable agents → credentials
```

Audit logs are recorded centrally regardless of registry.

---

## LOAD-BEARING dependency: Google group claims

**This is the single most important unproven assumption in the slice-2 model.**

The registry-per-client model collapses if Obot does not ingest Google Workspace group claims cleanly at OAuth login. Obot's documentation (as of v0.18.0) explicitly confirms dynamic group-claim ingestion for **Okta** and **JumpCloud**. For **Google Workspace and Microsoft Entra**, group-claim ingestion is **not explicitly documented**.

### Pilot gate (must pass before client data crosses this gateway)

1. Register Google Workspace OAuth client in Obot
2. Create two test groups in Workspace: `pilot-team-a`, `pilot-team-b`
3. Assign two test users, one to each group
4. Verify: Obot's user record for each test user shows the correct group membership *as a claim*, not via manual assignment
5. Verify: Obot's policy can scope a registry to one group and the other group cannot see it
6. Confirm: removing a user from a group revokes their registry access on the next login (or sooner)

**If any step fails:** stop slice-2 build. The isolation model needs a redesign (Workspace API polling? manual group sync? a different gateway?) before any client data crosses this layer.

---

## Audit

| Slice | Implementation |
|---|---|
| Slice 1 | Obot's built-in Postgres audit log. Queryable in Admin UI. Sufficient for single-user verification. |
| Slice 2 | Same Postgres log, plus a **planned sprint** to export to a WPP-sanctioned SIEM. **Non-trivial integration**: schema mapping, retention policy, ETL ownership, sink sanctioning, test coverage for silent drops. Do not assume this is a one-day add-on. |

Known bug to track: Obot Issue [#5907](https://github.com/obot-platform/obot/issues/5907) causes "Unknown User" entries in audit logs on Kubernetes/Helm deployments when Nanobot triggers MCP calls. Audit integrity is currently questionable in that deploy mode; confirm fix before relying on K8s audit records.

---

## Open questions to resolve at CO onboarding

1. **WPP SSO layer:** Does CO Workspace sit behind a WPP-wide SSO (e.g., WPP Open / Entra), or is Google direct? If the former, the OIDC client registers against the WPP layer, not Workspace.
2. **Group source of truth:** Are team/client groups maintained in Google Workspace, an HRIS, or informally? Slice-2 isolation needs a single canonical group source.
3. **Compliance posture:** Does WPP / GroupM compliance require audit logs in a specific SIEM with a specific retention window? Answers the SIEM-export sprint scope.
4. **OAuth provisioning rights:** Does Mal have rights to register an OIDC client in CO Workspace as Innovation Lead, or is provisioning gated behind a WPP IT ticket?
5. **Multi-tenant boundary:** If CO ever serves competing brands from the same Obot instance, does Obot's session-isolation + registry model meet the data-boundary bar? Obot's docs do not promise a first-class multi-tenancy model — re-evaluate at Obot v1.0.

---

## What is NOT built in slice 1

- No multi-user roles
- No client isolation enforcement
- No SSO to CO Workspace
- No group-claim ingestion
- No SIEM export pipeline

These are all designed above. The slice-1 build deliberately avoids them so that adding them later is a registration step, not a redesign.
