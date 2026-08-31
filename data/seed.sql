-- Sample data for the Tasklet support demo.
-- 5 users, 100 tickets distributed across all 5 categories, 4 priorities,
-- and 5 statuses, with mixed creation dates so date-range queries return
-- meaningful results.
--
-- Dates use SQLite's datetime('now', '-N days') so the seed always feels
-- fresh: re-running this script today produces tickets aged relative to
-- today. updated_at is set equal to created_at on seed rows for simplicity.

INSERT INTO users (id, email, name, created_at) VALUES
    (1, 'alice@northwind.example',  'Alice Chen',       datetime('now', '-90 days')),
    (2, 'marcus@globex.example',    'Marcus Patel',     datetime('now', '-75 days')),
    (3, 'sofia@initech.example',    'Sofia Rodriguez',  datetime('now', '-60 days')),
    (4, 'yuki@umbrella.example',    'Yuki Tanaka',      datetime('now', '-45 days')),
    (5, 'david@hooli.example',      'David Müller',     datetime('now', '-30 days'));

-- Tickets for Alice Chen (user 1) — frontend dev, mostly bug reports
INSERT INTO tickets (user_id, title, description, category, priority, status, created_at, updated_at) VALUES
    (1, 'Dashboard crashes on Safari', 'After upgrading to Safari 17 the dashboard goes blank 2s after load. Console shows a CORS preflight failure for /api/me.', 'bug_report', 'urgent', 'open', datetime('now', '-1 days'), datetime('now', '-1 days')),
    (1, 'Sprint board column drag broken', 'Dragging a column to reorder snaps it back. Started a few days ago on Chrome.', 'bug_report', 'high', 'in_progress', datetime('now', '-5 days'), datetime('now', '-5 days')),
    (1, 'Add WIP limits to board columns', 'Want to cap how many tickets can sit in a column. Useful for our flow.', 'feature_request', 'medium', 'open', datetime('now', '-2 days'), datetime('now', '-2 days')),
    (1, 'Tooltip flickers on hover', 'Status pill tooltip flickers if I hover near the edge.', 'bug_report', 'low', 'resolved', datetime('now', '-16 days'), datetime('now', '-16 days')),
    (1, 'How to invite teammates from Slack', 'Is there a Slack slash command to invite people, or do I always have to use the web UI?', 'how_to_question', 'low', 'closed', datetime('now', '-22 days'), datetime('now', '-22 days')),
    (1, 'Jira sync stops mid-import', 'Importing 400 tickets from Jira; sync halts at ~120 with no error toast.', 'integration_issue', 'high', 'waiting_on_customer', datetime('now', '-7 days'), datetime('now', '-7 days')),
    (1, 'Notifications double-firing', 'Comment mentions trigger two emails — one immediately and one ~30s later.', 'bug_report', 'medium', 'in_progress', datetime('now', '-4 days'), datetime('now', '-4 days')),
    (1, 'Bulk archive completed tasks', 'Need a way to archive all done tickets in a sprint at once. Doing it one-by-one is painful.', 'feature_request', 'high', 'open', datetime('now', '-1 days'), datetime('now', '-1 days')),
    (1, 'Kanban board fails to load with 500 errors', 'Around 9am ET on April 1 the board returned 500s for ~20 minutes.', 'bug_report', 'urgent', 'resolved', datetime('now', '-25 days'), datetime('now', '-25 days')),
    (1, 'How to export sprint reports as PDF', 'Need to share retros with leadership in PDF, can the export do this?', 'how_to_question', 'low', 'resolved', datetime('now', '-32 days'), datetime('now', '-32 days')),
    (1, 'Annual plan renewal question', 'Got a renewal email but the seat count looks wrong — we removed two users last quarter.', 'billing', 'medium', 'closed', datetime('now', '-42 days'), datetime('now', '-42 days')),
    (1, 'Time tracker resets at midnight', 'If a tracked task is running across midnight, the timer resets to 0 instead of continuing.', 'bug_report', 'high', 'open', datetime('now'), datetime('now')),
    (1, 'GitHub PR comments not syncing', 'PR comments stopped appearing in linked tickets a week ago. Other Github events still work.', 'integration_issue', 'medium', 'resolved', datetime('now', '-19 days'), datetime('now', '-19 days')),
    (1, 'Dark mode for sprint board', 'Long planning sessions are rough on my eyes. Dark theme please.', 'feature_request', 'low', 'open', datetime('now', '-8 days'), datetime('now', '-8 days')),
    (1, 'Mentions not triggering email', 'Mentioned a user in a comment, no email arrived. They have notifications on.', 'bug_report', 'medium', 'waiting_on_customer', datetime('now', '-4 days'), datetime('now', '-4 days')),
    (1, 'How to reorder sidebar items', 'Cannot find a way to drag-reorder my pinned projects in the sidebar.', 'how_to_question', 'low', 'resolved', datetime('now', '-55 days'), datetime('now', '-55 days')),
    (1, 'Filter bar collapses unexpectedly', 'Apply a filter, switch tabs, come back — filter bar is collapsed and selection lost.', 'bug_report', 'high', 'in_progress', datetime('now', '-6 days'), datetime('now', '-6 days')),
    (1, 'Custom statuses per project', 'Different teams use different workflows. Per-project status sets would help.', 'feature_request', 'medium', 'open', datetime('now', '-10 days'), datetime('now', '-10 days')),
    (1, 'Slack webhook intermittent', 'Tasklet to Slack webhook drops ~30% of events. Slack admin says no rate limits hit.', 'integration_issue', 'low', 'closed', datetime('now', '-45 days'), datetime('now', '-45 days')),
    (1, 'Cannot create new sprint — 403 error', 'Try to create a new sprint, get "403 Forbidden". I am the project admin.', 'bug_report', 'urgent', 'open', datetime('now', '-1 days'), datetime('now', '-1 days'));

-- Tickets for Marcus Patel (user 2) — PM, mostly feature requests and how-tos
INSERT INTO tickets (user_id, title, description, category, priority, status, created_at, updated_at) VALUES
    (2, 'How to set up cross-project rollups', 'Want a portfolio view that aggregates progress across 5 projects. Possible?', 'how_to_question', 'medium', 'resolved', datetime('now', '-12 days'), datetime('now', '-12 days')),
    (2, 'Recurring tasks support', 'Need tasks that auto-recreate weekly (eg standup notes). Currently I duplicate by hand.', 'feature_request', 'high', 'open', datetime('now', '-3 days'), datetime('now', '-3 days')),
    (2, 'Custom fields on tickets', 'Need a "customer impact" field with structured options. Tags are too loose.', 'feature_request', 'medium', 'in_progress', datetime('now', '-6 days'), datetime('now', '-6 days')),
    (2, 'Export filtered list as CSV', 'Filter view should have a CSV export that respects the active filters.', 'feature_request', 'medium', 'open', datetime('now', '-2 days'), datetime('now', '-2 days')),
    (2, 'How to bulk-assign tickets', 'I have 30 tickets to give to a new hire. Doing them one-by-one takes forever.', 'how_to_question', 'low', 'resolved', datetime('now', '-18 days'), datetime('now', '-18 days')),
    (2, 'Search ignores accents', 'Search for "Müller" misses entries spelled "Mueller" and vice versa.', 'bug_report', 'low', 'open', datetime('now', '-9 days'), datetime('now', '-9 days')),
    (2, 'How do priority weights work', 'Is "urgent" sorted strictly first, or is it weighted? Roadmap view shows odd order.', 'how_to_question', 'low', 'resolved', datetime('now', '-27 days'), datetime('now', '-27 days')),
    (2, 'Linked tickets not showing in roadmap', 'Tickets I link to a roadmap item are missing in the timeline view.', 'bug_report', 'medium', 'in_progress', datetime('now', '-5 days'), datetime('now', '-5 days')),
    (2, 'API rate limit too low for nightly export', 'Our nightly archive hits 429 around ticket 500. Need higher limit or paginate.', 'integration_issue', 'high', 'waiting_on_customer', datetime('now', '-8 days'), datetime('now', '-8 days')),
    (2, 'Two-factor authentication required', 'Org policy mandates 2FA. Tasklet does not enforce it for our workspace.', 'feature_request', 'urgent', 'open', datetime('now', '-4 days'), datetime('now', '-4 days')),
    (2, 'How to archive a project', 'Cannot find an archive option for old projects. Do I need to delete them?', 'how_to_question', 'low', 'closed', datetime('now', '-33 days'), datetime('now', '-33 days')),
    (2, 'Comment formatting strips line breaks', 'Multi-line comments get joined into one paragraph after submit.', 'bug_report', 'medium', 'resolved', datetime('now', '-21 days'), datetime('now', '-21 days')),
    (2, 'Per-team weekly digest emails', 'Want a Monday morning summary email for each team — what shipped, what is blocked.', 'feature_request', 'medium', 'open', datetime('now', '-1 days'), datetime('now', '-1 days')),
    (2, 'Plan upgrade — what is included in Scale tier', 'Looking at the pricing page; Scale tier features list is missing details.', 'billing', 'low', 'resolved', datetime('now', '-29 days'), datetime('now', '-29 days')),
    (2, 'Workflow automation broken after Tuesday update', 'Our "auto-close after 30 days" rule stopped firing after the April release.', 'bug_report', 'high', 'in_progress', datetime('now', '-3 days'), datetime('now', '-3 days')),
    (2, 'How to embed a board in Notion', 'Trying to embed a board view into a Notion page. Iframe just shows a login.', 'how_to_question', 'medium', 'waiting_on_customer', datetime('now', '-6 days'), datetime('now', '-6 days')),
    (2, 'Add task templates per project', 'Every PRD ticket follows the same skeleton. Templates would save us 10 minutes each.', 'feature_request', 'high', 'open', datetime('now', '-2 days'), datetime('now', '-2 days')),
    (2, 'Mobile app crashes on iOS 18 beta', 'Beta testers report the iOS app crash-loops on launch.', 'bug_report', 'urgent', 'open', datetime('now'), datetime('now')),
    (2, 'Connect with HubSpot', 'No native HubSpot integration. Customers want one — any plans?', 'integration_issue', 'low', 'open', datetime('now', '-14 days'), datetime('now', '-14 days')),
    (2, 'How to set keyboard shortcuts', 'Where are the keyboard shortcuts documented? The help search returns nothing.', 'how_to_question', 'low', 'closed', datetime('now', '-38 days'), datetime('now', '-38 days'));

-- Tickets for Sofia Rodriguez (user 3) — finance, billing-heavy
INSERT INTO tickets (user_id, title, description, category, priority, status, created_at, updated_at) VALUES
    (3, 'Invoice missing PO number', 'March invoice does not include the PO number we provided in our profile.', 'billing', 'high', 'open', datetime('now', '-4 days'), datetime('now', '-4 days')),
    (3, 'Annual prepay discount applied incorrectly', 'We prepaid for the year but our invoice shows monthly billing.', 'billing', 'urgent', 'in_progress', datetime('now', '-2 days'), datetime('now', '-2 days')),
    (3, 'Add VAT ID to billing profile', 'Need to add our EU VAT ID. The profile form has no VAT field.', 'billing', 'medium', 'resolved', datetime('now', '-22 days'), datetime('now', '-22 days')),
    (3, 'How to download all past invoices', 'Auditor wants 24 months of invoices. Downloading one at a time is brutal.', 'how_to_question', 'medium', 'resolved', datetime('now', '-18 days'), datetime('now', '-18 days')),
    (3, 'Seat overage charge surprise', 'Got billed for 12 over-seats this month. We never received an overage warning.', 'billing', 'urgent', 'waiting_on_customer', datetime('now', '-7 days'), datetime('now', '-7 days')),
    (3, 'Can we get NET-60 terms', 'Our AP team needs NET-60. Currently on NET-15. Who do I talk to?', 'billing', 'medium', 'open', datetime('now', '-3 days'), datetime('now', '-3 days')),
    (3, 'Refund for accidental seat purchase', 'Bought 5 extra seats by mistake yesterday. Need refund and seat removal.', 'billing', 'high', 'in_progress', datetime('now', '-1 days'), datetime('now', '-1 days')),
    (3, 'Tax exempt status not applied', 'We are a registered nonprofit. Tax-exempt cert was uploaded but tax still appears on invoice.', 'billing', 'high', 'open', datetime('now', '-5 days'), datetime('now', '-5 days')),
    (3, 'How to change billing email', 'Old AP person left. Need invoices to go to a new email address.', 'how_to_question', 'low', 'resolved', datetime('now', '-25 days'), datetime('now', '-25 days')),
    (3, 'Two charges for the same month', 'March was billed on March 1 AND March 28. Need one reversed.', 'billing', 'urgent', 'resolved', datetime('now', '-30 days'), datetime('now', '-30 days')),
    (3, 'Reports dashboard shows blank charts', 'All four charts on the reports dashboard render as empty SVGs.', 'bug_report', 'medium', 'open', datetime('now', '-2 days'), datetime('now', '-2 days')),
    (3, 'How to break out spend per team', 'Want a cost report by department. Current invoice is one line item.', 'how_to_question', 'medium', 'open', datetime('now', '-6 days'), datetime('now', '-6 days')),
    (3, 'SSO login fails for finance group', 'Our finance team OU cannot log in via SAML; everyone else can.', 'integration_issue', 'high', 'in_progress', datetime('now', '-4 days'), datetime('now', '-4 days')),
    (3, 'Add a budget cap feature', 'Want to set a hard cap on monthly seat spend so we never get a surprise.', 'feature_request', 'high', 'open', datetime('now', '-10 days'), datetime('now', '-10 days')),
    (3, 'CSV import of vendor list', 'Bulk-creating tickets for vendor onboarding. CSV import would help.', 'feature_request', 'low', 'closed', datetime('now', '-50 days'), datetime('now', '-50 days')),
    (3, 'Currency wrong on invoice', 'Invoice shows USD but our contract is EUR.', 'billing', 'urgent', 'resolved', datetime('now', '-19 days'), datetime('now', '-19 days')),
    (3, 'How to add a backup payment method', 'Want a fallback card in case the primary fails. Form only has one slot.', 'how_to_question', 'low', 'open', datetime('now', '-8 days'), datetime('now', '-8 days')),
    (3, 'Quote request for 50-seat upgrade', 'Need a written quote for moving from 20 to 70 seats next quarter.', 'billing', 'medium', 'waiting_on_customer', datetime('now', '-11 days'), datetime('now', '-11 days')),
    (3, 'Dashboard timezone wrong on reports', 'Daily totals show in UTC, our team is in CET. Causes off-by-one bugs in reports.', 'bug_report', 'medium', 'resolved', datetime('now', '-28 days'), datetime('now', '-28 days')),
    (3, 'How to set up DocuSign for contracts', 'Want renewal contracts signed via DocuSign. Is there an integration?', 'integration_issue', 'low', 'open', datetime('now', '-13 days'), datetime('now', '-13 days'));

-- Tickets for Yuki Tanaka (user 4) — DevOps, integration-heavy
INSERT INTO tickets (user_id, title, description, category, priority, status, created_at, updated_at) VALUES
    (4, 'GitHub Actions sync delay', 'Build status updates take 5-10 min to reflect on linked tickets.', 'integration_issue', 'high', 'in_progress', datetime('now', '-3 days'), datetime('now', '-3 days')),
    (4, 'GitLab MR auto-link broken', 'Pasting a GitLab MR into a comment used to auto-link; now it stays as plain text.', 'integration_issue', 'medium', 'open', datetime('now', '-5 days'), datetime('now', '-5 days')),
    (4, 'PagerDuty incident creates duplicate tickets', 'When PD escalates an incident, two tickets get created — one per escalation step.', 'integration_issue', 'urgent', 'in_progress', datetime('now', '-2 days'), datetime('now', '-2 days')),
    (4, 'How to set up SCIM with Okta', 'Following the docs and getting "invalid metadata" on the Okta side. Anyone seen this?', 'how_to_question', 'medium', 'resolved', datetime('now', '-18 days'), datetime('now', '-18 days')),
    (4, 'Webhook signature verification fails', 'Our receiver rejects Tasklet webhooks because the X-Signature header is empty.', 'integration_issue', 'high', 'waiting_on_customer', datetime('now', '-6 days'), datetime('now', '-6 days')),
    (4, 'API: get-ticket returns stale status', 'GET /tickets/{id} returns status from 30 seconds ago even after a status change.', 'bug_report', 'high', 'open', datetime('now', '-1 days'), datetime('now', '-1 days')),
    (4, 'Bulk endpoint missing for ticket updates', 'PATCHing 200 tickets one at a time is slow. Need a bulk endpoint.', 'feature_request', 'medium', 'open', datetime('now', '-8 days'), datetime('now', '-8 days')),
    (4, 'Datadog log forwarding cuts off long messages', 'Tasklet log lines >1KB get truncated when forwarded to Datadog.', 'integration_issue', 'low', 'resolved', datetime('now', '-22 days'), datetime('now', '-22 days')),
    (4, 'How to rotate API keys without downtime', 'Need to rotate our service token. Doc says revoke + create. Will in-flight requests fail?', 'how_to_question', 'medium', 'resolved', datetime('now', '-15 days'), datetime('now', '-15 days')),
    (4, 'OAuth scope expansion', 'Our integration needs to read attachments. Current scope does not include them.', 'feature_request', 'medium', 'in_progress', datetime('now', '-4 days'), datetime('now', '-4 days')),
    (4, 'API rate limit hit after release', 'Our nightly job started getting 429s after the April release. Did limits change?', 'integration_issue', 'urgent', 'open', datetime('now'), datetime('now')),
    (4, 'Slack channel pin breaks on long titles', 'Tickets pinned to a Slack channel show empty preview if title >100 chars.', 'bug_report', 'low', 'closed', datetime('now', '-40 days'), datetime('now', '-40 days')),
    (4, 'How to register an OAuth app for a customer', 'Customer wants to embed our integration. Need to create an OAuth app.', 'how_to_question', 'low', 'open', datetime('now', '-12 days'), datetime('now', '-12 days')),
    (4, 'CLI tool feature parity gap', 'tasklet-cli is missing the bulk-comment command available in the API.', 'feature_request', 'low', 'open', datetime('now', '-20 days'), datetime('now', '-20 days')),
    (4, 'Webhook delivery retry interval too short', 'Our flaky receiver gets 3 retries within 60s and gives up. Want exponential backoff.', 'integration_issue', 'medium', 'in_progress', datetime('now', '-5 days'), datetime('now', '-5 days')),
    (4, 'Audit log missing tool invocations', 'API calls show up in audit log but tool/integration calls do not.', 'feature_request', 'medium', 'open', datetime('now', '-7 days'), datetime('now', '-7 days')),
    (4, 'API docs missing rate-limit headers', 'Docs do not mention X-RateLimit-Remaining. Without it we cannot self-throttle.', 'feature_request', 'low', 'resolved', datetime('now', '-33 days'), datetime('now', '-33 days')),
    (4, 'How to detect breaking API changes', 'Is there a changelog feed or webhook for API deprecations?', 'how_to_question', 'medium', 'closed', datetime('now', '-47 days'), datetime('now', '-47 days')),
    (4, 'Linked Sentry events stop syncing', 'After 50 events the Sentry integration stops adding new linked errors.', 'integration_issue', 'high', 'waiting_on_customer', datetime('now', '-9 days'), datetime('now', '-9 days')),
    (4, 'CI deploy hooks not firing on tagged release', 'Deploy webhook fires on every push but skips tagged releases. Probably a regex bug.', 'bug_report', 'medium', 'open', datetime('now', '-2 days'), datetime('now', '-2 days'));

-- Tickets for David Müller (user 5) — ops generalist, mixed
INSERT INTO tickets (user_id, title, description, category, priority, status, created_at, updated_at) VALUES
    (5, 'New user invite email never arrives', 'Invited 3 users yesterday, none received the email. Spam folder is empty.', 'bug_report', 'high', 'open', datetime('now', '-1 days'), datetime('now', '-1 days')),
    (5, 'Roadmap milestones disappearing', 'Created 4 milestones for Q3, only 2 visible after refresh.', 'bug_report', 'medium', 'in_progress', datetime('now', '-3 days'), datetime('now', '-3 days')),
    (5, 'How to grant read-only access to a guest', 'Need to share a board with an external auditor as view-only. Cannot find guest role.', 'how_to_question', 'medium', 'resolved', datetime('now', '-14 days'), datetime('now', '-14 days')),
    (5, 'Add scheduled reports via email', 'Want a Monday-morning report email summarizing last week per team.', 'feature_request', 'medium', 'open', datetime('now', '-6 days'), datetime('now', '-6 days')),
    (5, 'Automation rule editor dropdown clipped', 'In the rule editor the action dropdown is cut off below the fold.', 'bug_report', 'low', 'open', datetime('now', '-4 days'), datetime('now', '-4 days')),
    (5, 'How to bulk-tag old tickets', 'We renamed a project. 200 old tickets need a new tag. Web UI bulk-tag is missing.', 'how_to_question', 'medium', 'waiting_on_customer', datetime('now', '-7 days'), datetime('now', '-7 days')),
    (5, 'SAML metadata URL changed', 'Our IdP rotated the SAML metadata URL. Where do I update it on Tasklet?', 'integration_issue', 'high', 'in_progress', datetime('now', '-2 days'), datetime('now', '-2 days')),
    (5, 'Markdown image upload fails for >5MB', 'Pasting a screenshot >5MB returns "upload failed" with no other detail.', 'bug_report', 'medium', 'resolved', datetime('now', '-16 days'), datetime('now', '-16 days')),
    (5, 'Domain capture for new signups', 'Want anyone with @hooli.example to auto-join our workspace. Cannot find this setting.', 'feature_request', 'medium', 'open', datetime('now', '-10 days'), datetime('now', '-10 days')),
    (5, 'How to view session log for a user', 'Auditor wants login history per user. Where is this in the admin panel?', 'how_to_question', 'low', 'resolved', datetime('now', '-23 days'), datetime('now', '-23 days')),
    (5, 'Charge for canceled seat', 'Removed a seat 3 weeks ago, this month invoice still includes it.', 'billing', 'high', 'open', datetime('now', '-3 days'), datetime('now', '-3 days')),
    (5, 'Search latency 8s+ on large workspace', 'Search takes 8-15s on workspaces over 50k tickets. Was instant a month ago.', 'bug_report', 'high', 'in_progress', datetime('now', '-5 days'), datetime('now', '-5 days')),
    (5, 'How to disable email notifications globally', 'Onboarding new team — want to silence emails until they configure prefs themselves.', 'how_to_question', 'low', 'closed', datetime('now', '-41 days'), datetime('now', '-41 days')),
    (5, 'Integration with 1Password for service accounts', 'We store service tokens in 1Password. Native integration would beat manual rotation.', 'integration_issue', 'low', 'open', datetime('now', '-19 days'), datetime('now', '-19 days')),
    (5, 'Add native time zone per user', 'Multi-region team — due dates show in workspace TZ, not user TZ. Confusing.', 'feature_request', 'medium', 'open', datetime('now', '-8 days'), datetime('now', '-8 days')),
    (5, 'Org admin cannot remove other admin', 'I am org owner but cannot remove a former admin. Trash icon greyed out.', 'bug_report', 'urgent', 'in_progress', datetime('now', '-2 days'), datetime('now', '-2 days')),
    (5, 'How to merge two duplicate workspaces', 'Two teams set up Tasklet independently. We want to merge them. Possible?', 'how_to_question', 'medium', 'open', datetime('now', '-11 days'), datetime('now', '-11 days')),
    (5, 'Workspace export missing attachments', 'JSON export contains tickets but not the uploaded files.', 'bug_report', 'medium', 'waiting_on_customer', datetime('now', '-6 days'), datetime('now', '-6 days')),
    (5, 'Per-project Slack channel mapping', 'Right now all projects post to one Slack channel. Want one channel per project.', 'feature_request', 'high', 'open', datetime('now', '-1 days'), datetime('now', '-1 days')),
    (5, 'Cannot revoke service token from UI', 'Created an API token, the UI no longer shows it; cannot revoke without DB access.', 'bug_report', 'urgent', 'open', datetime('now'), datetime('now'));
