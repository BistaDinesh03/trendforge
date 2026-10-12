# Launch checklist

Each `generated/YYYY-MM-DD-<slug>/` directory is a scaffold, not a finished
product. Before you launch one:

1. **Read the idea.** The scaffold's `README.md` carries the problem
   statement, MVP features, tech stack, 7-day plan, and launch plan that were
   written for that day's analysis.
2. **Check the analysis.** The matching daily report
   (`reports/YYYY-MM-DD.md`) explains why the source repository trended, which
   complaints its users repeat, and how its license was classified
   (permissive, copyleft, or none).
3. **Keep the provenance.** The scaffold ships an MIT `LICENSE` and a
   Provenance section stating that the design came from metadata, not copied
   code. Keep both intact if you rebrand.
4. **Set it up:** `make setup`, then `make run`. Verify `GET /health` on
   `127.0.0.1:8000` returns `{"service": "...", "status": "ok"}`.
5. **Pass the gates:** `make test` and `make lint` before pushing anywhere.
6. **Push to a new repository**, including the bundled
   `.github/dependabot.yml` so dependency updates keep arriving.
7. **Configure secrets:** copy `.env.example` to `.env`; never commit real
   values.
8. **Work the 7-day plan** in the scaffold README, then revisit
   [health-checklist.md](health-checklist.md).
