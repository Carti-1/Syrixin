# Git Workflow

## Branch per feature

Every change must be made on a dedicated branch. Never commit directly to `main` or `develop`.

### Naming convention

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/<short-description>` | `feat/continuous-monitoring` |
| Bug fix | `fix/<short-description>` | `fix/battery-status-none` |
| Tests | `test/<short-description>` | `test/failure-scenarios` |
| Docs / chore | `chore/<short-description>` | `chore/update-readme` |

### Workflow

1. Create a branch from `develop`: `git checkout -b feat/<name> develop`
2. Implement and commit on that branch
3. Open a PR into `develop` when done
4. `main` receives only stable, reviewed code from `develop`

### Commit messages

Follow Conventional Commits:
- `feat:` — new functionality visible to the user
- `fix:` — bug fix
- `test:` — adding or updating tests
- `refactor:` — code restructuring without behavior change
- `chore:` — tooling, config, docs, dependencies

Keep the subject line under 72 characters. Use the body for details when needed.
