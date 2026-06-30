# Frontend Interaction Audit

This document inventories every interactive control in the Batch 1 frontend prototype (`frontend/src/App.jsx` and `frontend/src/data.js`).

## Summary counts

| Category | Count |
|---|---|
| Navigation controls | 12 |
| Search / filter controls | 18 |
| Home / prompt controls | 10 |
| Object detail controls | 12 |
| Lineage controls | 7 |
| Gap controls | 9 |
| Proposal controls | 17 |
| Utility / chrome controls | 6 |
| **Total interactive controls** | **91** |

## Controls table

| Location | Control text / aria-label | Current behavior | Intended behavior | Backend-dependent |
|---|---|---|---|---|
| Sidebar | Home, Models, Lineage, Gaps, Proposals nav items | `navigate(id)` to route | Keep — primary route navigation | No |
| Sidebar | Close navigation (mobile scrim) | Closes mobile sidebar | Keep — close mobile nav | No |
| Topbar | Open navigation | Opens mobile sidebar | Keep — open mobile nav | No |
| Topbar | Search model input | Sets query, submit navigates to `#/models?search=...` | Keep — global search input | Yes (real search) |
| Topbar | Close search | Collapses search field | Keep — dismiss search | No |
| Topbar | Notifications | Shows toast (utilityActions) | Disable or wire to notifications backend | Yes |
| Topbar | Profile button | Toggles profile menu | Keep — local menu toggle | No |
| Topbar | Profile | Shows toast | Disable or wire to profile page | Yes |
| Topbar | Preferences | Shows toast | Disable or wire to preferences | No |
| Topbar | Switch repository | Shows toast | Disable or wire to repo switcher | Yes |
| Home | Ask question textarea | Sets prompt state | Keep — prompt input | No |
| Home | Attach context | Shows toast | Disable until context picker exists | No |
| Home | Context | Shows toast | Disable or wire to context picker | No |
| Home | Ask Martenweave | Runs fake 650 ms "thinking" then shows answer | Keep as local demo; real version calls AI backend | Yes |
| Home | Suggested questions chips | Submits suggested prompt | Keep — local prompt shortcuts | No |
| Home | Open gaps insight card | `navigate("gaps")` | Keep — navigate to gaps | No |
| Home | Impacted systems insight card | `navigate("lineage")` | Keep — navigate to lineage | No |
| Home | Recommended action insight card | `navigate("proposal")` | Keep — navigate to proposal #27 (demo default) | No |
| Home | View all (affected fields) | `navigate("gaps")` | Keep — navigate to gaps | No |
| Home | Recent objects rail items | `navigate("object")` | **Wire** to `navigate("object", { id: item.id })` | No |
| Home | View all (recent objects) | `navigate("models")` | Keep — navigate to models | No |
| Models | Global search input | Filters local results | Keep — local search filter | No |
| Models | Clear search (×) | Clears query | Keep — clear search | No |
| Models | Search submit | No-op (`event.preventDefault()`) | Keep or remove (client-side filter) | No |
| Models | Tabs: All, Objects, Fields, Mappings, Proposals | Filters by category | Keep — category filter | No |
| Models | Ask follow-up | `navigate("home")` | Keep — return to ask view | No |
| Models | Sorted by select | Changes sort order | Keep — local sort | No |
| Models | Filters toggle | Opens/closes filter panel | Keep — toggle filters | No |
| Models | Object type checkboxes | Filter by type | Keep — local type filter | No |
| Models | Status checkboxes | Filter by status | Keep — local status filter | No |
| Models | Clear all (filters) | Resets filters | Keep — reset filters | No |
| Models | Result row | `navigate("object")` / `navigate("proposal")` | **Wire** to `navigate(..., { id: item.id })` | No |
| Models | Clear search (empty state) | Resets query/filters | Keep — reset search | No |
| Object | Back to search | `navigate("models")` | Keep — return to search | No |
| Object | Copy ID | Copies hard-coded `DOMAIN-CUSTOMER-BP` | **Use** looked-up object ID | No |
| Object | Export | Shows toast | Disable or wire to export backend | Yes |
| Object | Trace lineage | `navigate("lineage")` | Keep — navigate to lineage | No |
| Object | More actions (⋮) | Shows toast (no menu) | Remove or implement menu | No |
| Object | Overview / Fields / Relationships / Governance tabs | Switches tab state | Keep — local tabs | No |
| Object | View all fields | No-op button | Wire to Fields tab or remove | No |
| Object | Review open gaps | `navigate("gaps")` | Keep — navigate to gaps | No |
| Object | Connected system rows | `navigate("lineage")` | Keep — navigate to lineage | No |
| Object | Fields table rows | No-op buttons | Wire to field detail when it exists | No |
| Object | Relationship cards | `navigate("lineage")` | Keep — navigate to lineage | No |
| Lineage | Export | Shows toast | Disable or wire to export backend | Yes |
| Lineage | View object | `navigate("object")` | **Wire** to current selected object ID | No |
| Lineage | Depth select | Sets depth state (no effect on graph) | Keep or connect to graph filter | No |
| Lineage | Filters | Shows toast | Disable or implement lineage filters | Yes |
| Lineage | Panel toggle | Opens/closes inspector | Keep — local panel toggle | No |
| Lineage | ReactFlow node clicks | Selects node, opens inspector | Keep — local selection | No |
| Lineage | Open object details | `navigate("object")` | **Wire** to selected node ID | No |
| Lineage | Review related gaps | `navigate("gaps")` | Keep — navigate to gaps | No |
| Gaps | Search gaps input | Filters local gaps | Keep — local gap search | No |
| Gaps | Severity select | Filters by severity | Keep — local severity filter | No |
| Gaps | Sort select | Changes sort order (no-op on render) | Keep or implement sort | No |
| Gaps | More filters | Shows toast | Disable or implement filters | Yes |
| Gaps | Create issue | Shows toast | Disable or wire to issue creation backend | Yes |
| Gaps | Gap card expand/collapse | Toggles `expandedId` | Keep — local expand | No |
| Gaps | View details | No-op button | Wire to gap detail when it exists | No |
| Gaps | Review proposal / Create proposal | `navigate("proposal")` / `navigate("proposals")` | **Wire** to linked proposal ID | Yes (proposal lookup) |
| Gaps | Recommended Review proposal | `navigate("proposal")` | **Wire** to the dynamic recommended proposal ID (`recommendedProposal.id`) | No |
| Proposals | All / In review / Draft / Approved tabs | Filters by status | Keep — local status filter | No |
| Proposals | Search proposals input | Filters local proposals | Keep — local proposal search | No |
| Proposals | New proposal | Shows toast | Disable or wire to proposal creation | Yes |
| Proposals | Proposal row | `navigate("proposal")` | **Wire** to `navigate("proposal", { id: proposal.id })` | No |
| Proposal | Back to proposals | `navigate("proposals")` | Keep — return to list | No |
| Proposal | Request changes | Opens reject dialog | Keep — local review decision | Yes (approval backend) |
| Proposal | Approve proposal | Opens approve dialog | Keep — local review decision | Yes (approval backend) |
| Proposal | Changes / Impact / Validation / Activity tabs | Switches tab state | Keep — local tabs | No |
| Proposal | Side by side / Unified view toggle | Toggles diff view | Keep — local view toggle | No |
| Proposal | Linked gap | `navigate("gaps")` | **Wire** to linked gap ID when available | No |
| Proposal | Add note | Saves comment locally | Keep — local comment draft | Yes (persistence backend) |
| Decision dialog | Close (×) | Closes dialog | Keep — cancel decision | No |
| Decision dialog | Cancel | Closes dialog | Keep — cancel decision | No |
| Decision dialog | Approve / Request changes | Closes dialog, navigates back | Keep — local demo confirmation | Yes (approval backend) |

## Backend-dependent actions

These actions currently use local state or demo data. A production implementation requires backend integration:

1. **Global search** — query canonical index / SQLite backend.
2. **Notifications** — fetch and mark user notifications.
3. **Profile / Preferences / Switch repository** — user identity and repository switching.
4. **AI prompt answer** — call the AI patch proposal / analysis service.
5. **Export** — generate CSV/JSON/audit export from the backend.
6. **Create issue / New proposal / Approve proposal / Request changes** — mutate canonical state through the change-request pipeline.
7. **Lineage filters / More filters** — query lineage edges and gap metadata from the backend.
8. **Add note** — persist proposal review comments.
9. **Gap → proposal navigation** — resolve linked proposal IDs from backend data.
