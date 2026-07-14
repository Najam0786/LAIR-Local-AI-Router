# LAIR Release Checklist

This checklist must be completed before every tagged release.

---

# Phase 1 — Planning

- [ ] Define release objectives.
- [ ] Review ROADMAP.md.
- [ ] Review Architecture Handbook.
- [ ] Finalize implementation scope.

---

# Phase 2 — Development

- [ ] Complete implementation.
- [ ] Compile modified Python files.
- [ ] Integrate changes.
- [ ] Review code quality.
- [ ] Remove dead code.

---

# Phase 3 — Testing

- [ ] Run application.
- [ ] Verify startup.
- [ ] Test `/`.
- [ ] Test `/health`.
- [ ] Test `/models`.
- [ ] Test `/route`.
- [ ] Verify Swagger documentation.

---

# Phase 4 — Documentation

- [ ] Update README.md.
- [ ] Update ROADMAP.md.
- [ ] Update CHANGELOG.md.
- [ ] Review Architecture Handbook.
- [ ] Verify version numbers.

---

# Phase 5 — Repository

- [ ] `git status`
- [ ] Review modified files.
- [ ] Stage changes.
- [ ] Create commit.
- [ ] Push branch.

---

# Phase 6 — Release

- [ ] Create Git tag.
- [ ] Push tag.
- [ ] Create GitHub Release.
- [ ] Publish release notes.

---

# Phase 7 — Post Release

- [ ] Verify GitHub Release.
- [ ] Verify repository documentation.
- [ ] Update next milestone.
- [ ] Begin next sprint.

---

# Engineering Principle

Every release must satisfy:

✔ Builds successfully

✔ Passes API verification

✔ Documentation updated

✔ Architecture updated

✔ Repository clean

✔ Tagged

✔ Released