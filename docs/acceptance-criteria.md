# Acceptance Criteria

- [ ] Create service requests with category and priority
- [ ] Route requests through multi-step approval chains
- [ ] Enforce role-based approval and prevent invalid state transitions
- [ ] Persist comments and audit events
- [ ] Filter and paginate request listings
- [ ] Report status counts and overdue approvals

## Cross-cutting
- [ ] Unauthorized requests are rejected.
- [ ] Invalid input returns a clear 4xx response.
- [ ] Data persists across application restarts.
- [ ] List endpoints bound pagination.
- [ ] Duplicate submissions are handled consistently.
- [ ] Tests cover success paths, permission failures and edge cases.
