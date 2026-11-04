# Teha access contract

Authorization uses live rows in `teha_access_roles`, never user-editable Auth metadata. Only the existing sole owner can administer accounts through the validated Edge endpoint. The database table accepts doctor, reception, management or blocked; admin is derived from the pinned owner's UUID, confirmed email and membership. Unassigned users are blocked. Role changes take effect at the next SQL statement without waiting for JWT refresh; the UI polls permissions every 15 seconds.

| Profile | Modules |
|---|---|
| Owner admin | All modules and change history |
| Doctor | Patients, appointments, triage, notes, teeth, treatments, documents |
| Reception | Patients, appointments, triage |
| Management | Reports, finance, team |

Limited lookup projections supply provider names/registration to clinical workflows and patient names to finance. They never include the full team or clinical record. Management reports use aggregate appointment/treatment counts. Profile settings remain writable by the account; clinic settings are writable only by management/admin. Backup UI is admin-only; imports still run under RLS.

This change retains the existing per-account owner_id boundary. It does not merge workspaces or implement shared clinic membership. Account role is separate from the informational team record.

Apply schema.sql on a new deployment, then roles.sql. The production changes were applied through named migrations `teha_live_role_permissions_and_admin_history` and `teha_hide_privileged_access_lookup`. SQL regression script roles-test.sql runs all fixtures/role updates in a transaction ending in rollback. Run it on the configured Clinica project; the pinned owner must already exist. Admin endpoint tests: npm test in admin/. Frontend tests: npm test in web/.

The privileged lookup and record validation stay in the private schema; public teha_access is an invoker wrapper. The validator authenticates the row owner and preserves clinical append-only rules; RLS authorizes reads/writes by store. Anonymous callers receive no access. History remains append-only and is readable only by the pinned admin.
