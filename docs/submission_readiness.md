# Submission readiness against the external guidelines

The four-page PDF gives submission and packaging requirements. It does not define a technical Module B rubric, model score threshold, or required dataset size. This checklist distinguishes the product prototype from final submission packaging.

| PDF requirement | Current state | Remaining work |
|---|---|---|
| Working source code, architecture, dependencies, and exact run commands | Present in `src/`, `requirements*.txt`, `README.md`, and `docs/architecture.png` | Recheck commands from a clean install before submission; public repository is not configured in this workspace. |
| Public GitHub repository | Not configured or verified; this workspace has no Git metadata | Create/publish the named public repository and verify access in a private browser window. |
| Mandatory README template | Project overview, architecture, datasets, setup, and results are present | Fill in candidate name, college email, campus, and public demo/deck links. |
| 5–7 slide PDF/PPTX | Six-slide PDF and PPTX exist; model target, data, holdout result, and limitations now match the trained artifacts | Fill candidate/deck link details before public submission. |
| 10-minute unlisted YouTube demo | Not submitted | Record the running end-to-end prototype and verify the unlisted link in a private browser window. |
| Data/source files and provenance | Synthetic portfolio/news and public RSS snapshot are in `data/`; sources/assumptions are documented | The 1.51 GiB public EDT training source is intentionally not copied into the repository; the notebook downloads it from the cited mirror. Do not add confidential client data. |
| `LICENSE` | Present | Keep the license aligned with your intended public release. |
| Repository name/hygiene | No Git repository metadata in this workspace; large benchmark data is excluded | Use the requested `<college>-<candidate-name>-hackathon` public repo name and retain the download-on-demand approach for large data. |
| Live jury pitch and Q&A | Future event requirement | Be prepared to explain data assumptions, model limits, stress shocks, and architecture. |
| AI integrity, individual submission, confidentiality, and deadline | Requirements read | Disclose assistance honestly, submit as an individual, use only public/synthetic data, and meet the communicated deadline. |

The guidelines also recommend a 5–7 slide story covering problem/approach, system design, implementation, results, domain impact, and optional limitations; a roughly 10-minute video showing setup, end-to-end use, and results; clear permissions for shared assets; incremental commits; and final submission through the official form. Slide/video work was deferred while the working prototype is being stabilized.
