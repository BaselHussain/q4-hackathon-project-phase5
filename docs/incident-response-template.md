# Incident Response Template

Use this template to document incidents and conduct post-mortems.

---

## Incident Report #[NUMBER]

**Date**: [YYYY-MM-DD]
**Time**: [HH:MM UTC]
**Duration**: [X hours Y minutes]
**Severity**: [Critical / High / Medium / Low]
**Status**: [Investigating / Mitigated / Resolved / Closed]

---

## Summary

[Brief 1-2 sentence description of the incident]

---

## Impact

### User Impact
- **Users Affected**: [Number or percentage]
- **Services Affected**: [List of affected services]
- **Functionality Impacted**: [What features were unavailable/degraded]

### Business Impact
- **Revenue Impact**: [Estimated $ or N/A]
- **SLO Impact**: [Which SLOs were breached, error budget consumed]
- **Customer Complaints**: [Number of support tickets/complaints]

---

## Timeline

All times in UTC.

| Time | Event |
|------|-------|
| HH:MM | [First indication of problem - alert fired, user report, etc.] |
| HH:MM | [Incident declared, on-call engineer paged] |
| HH:MM | [Investigation started] |
| HH:MM | [Root cause identified] |
| HH:MM | [Mitigation applied] |
| HH:MM | [Service restored] |
| HH:MM | [Incident resolved] |
| HH:MM | [Post-mortem scheduled] |

---

## Detection

**How was the incident detected?**
- [ ] Automated alert (Prometheus/Alertmanager)
- [ ] User report
- [ ] Internal monitoring
- [ ] Other: [Specify]

**Alert Name**: [If applicable]
**Detection Time**: [Time from incident start to detection]

---

## Root Cause

### What Happened

[Detailed technical explanation of what went wrong]

### Why It Happened

[Underlying cause - code bug, configuration error, capacity issue, etc.]

### Contributing Factors

- [Factor 1]
- [Factor 2]
- [Factor 3]

---

## Resolution

### Immediate Actions Taken

1. [Action 1 - e.g., Rolled back deployment]
2. [Action 2 - e.g., Scaled up replicas]
3. [Action 3 - e.g., Restarted service]

### Commands Executed

```bash
# Document exact commands used for resolution
kubectl rollback deployment backend
kubectl scale deployment backend --replicas=5
```

### Why Resolution Worked

[Explanation of why the mitigation resolved the issue]

---

## Lessons Learned

### What Went Well

- [Positive aspect 1 - e.g., Alert fired quickly]
- [Positive aspect 2 - e.g., Team responded promptly]
- [Positive aspect 3 - e.g., Rollback was smooth]

### What Went Poorly

- [Issue 1 - e.g., Root cause took too long to identify]
- [Issue 2 - e.g., Runbook was outdated]
- [Issue 3 - e.g., Communication was unclear]

### Where We Got Lucky

- [Lucky break 1 - e.g., Incident occurred during low traffic period]
- [Lucky break 2 - e.g., Backup system kicked in automatically]

---

## Action Items

| Action Item | Owner | Priority | Due Date | Status |
|-------------|-------|----------|----------|--------|
| [Fix root cause in code] | [@engineer] | P0 | [YYYY-MM-DD] | [ ] |
| [Update monitoring/alerting] | [@engineer] | P1 | [YYYY-MM-DD] | [ ] |
| [Update runbook] | [@engineer] | P2 | [YYYY-MM-DD] | [ ] |
| [Add integration test] | [@engineer] | P1 | [YYYY-MM-DD] | [ ] |
| [Improve documentation] | [@engineer] | P2 | [YYYY-MM-DD] | [ ] |

**Priority Levels**:
- P0: Critical - Must be done before next release
- P1: High - Should be done within 1 week
- P2: Medium - Should be done within 1 month
- P3: Low - Nice to have

---

## Prevention

### Short-term Fixes (< 1 week)

1. [Fix 1]
2. [Fix 2]
3. [Fix 3]

### Long-term Improvements (< 1 month)

1. [Improvement 1]
2. [Improvement 2]
3. [Improvement 3]

### Monitoring/Alerting Improvements

- [ ] Add new alert for [specific condition]
- [ ] Adjust alert threshold for [existing alert]
- [ ] Create dashboard for [specific metric]
- [ ] Add logging for [specific event]

---

## Communication

### Internal Communication

- **Incident Channel**: [Slack channel or communication tool]
- **Status Updates**: [How often were updates provided]
- **Stakeholders Notified**: [List of people/teams notified]

### External Communication

- **Customer Notification**: [Yes/No - If yes, when and how]
- **Status Page Update**: [Yes/No - If yes, link to update]
- **Support Ticket Response**: [Template used for responding to tickets]

---

## Metrics

### SLO Impact

| SLO | Target | Actual | Error Budget Consumed |
|-----|--------|--------|----------------------|
| API Availability | 99.9% | [X%] | [Y%] |
| Response Time p95 | 500ms | [Xms] | N/A |

### Incident Metrics

- **Time to Detect (TTD)**: [X minutes]
- **Time to Acknowledge (TTA)**: [X minutes]
- **Time to Mitigate (TTM)**: [X minutes]
- **Time to Resolve (TTR)**: [X hours]

---

## Related Incidents

- [Link to similar incident #123]
- [Link to related incident #456]

---

## Attachments

- [Link to logs]
- [Link to metrics dashboard]
- [Link to code changes]
- [Link to runbook updates]

---

## Post-Mortem Meeting

**Date**: [YYYY-MM-DD]
**Attendees**: [List of attendees]
**Recording**: [Link to recording if available]

### Key Discussion Points

1. [Point 1]
2. [Point 2]
3. [Point 3]

### Decisions Made

1. [Decision 1]
2. [Decision 2]
3. [Decision 3]

---

## Sign-off

**Incident Commander**: [Name] - [Date]
**Engineering Manager**: [Name] - [Date]
**Product Manager**: [Name] - [Date]

---

## Template Version

Version: 1.0
Last Updated: 2024-01-15
