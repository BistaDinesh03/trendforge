# Health checklist

For a generated project - or any small repository - re-run these checks when
you ship.

## Every pull request

- [ ] `make test` passes (`python -m pytest -q`)
- [ ] `make lint` is clean (`ruff check .` and `ruff format --check .`)
- [ ] No secrets in the diff (`.env` is git-ignored)

## Weekly

- [ ] Dependabot pull requests reviewed (every scaffold ships
  `.github/dependabot.yml`)
- [ ] `GET /health` still answers on the running service
- [ ] `SECURITY.md` still matches how you want vulnerability reports delivered

## Repository hygiene

- [ ] README has a one-line pitch and copy-pasteable install instructions
- [ ] A lockfile is committed so installs are reproducible
- [ ] CI runs the tests (scaffolds ship a Dependabot config but no workflow -
  add `.github/workflows/` that runs `make test`)
- [ ] The LICENSE file matches what you intend to publish
