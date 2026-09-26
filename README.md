# Ferroelectric Memory to AI

From materials physics to memory systems and AI infrastructure.

**[Read the course as web pages](https://az9713.github.io/ferroelectric-memory-to-ai/)**

An independent graduate-level learning program connecting materials physics, ferroelectric devices, memory arrays, digital implementation, AI workloads, and data-center energy. Ten chapters and a capstone include worked examples, complete exercise solutions, source provenance, and executable projects.

## Start here

- [15-minute research overview](https://az9713.github.io/ferroelectric-memory-to-ai/overview.html)
- [Curriculum and prerequisite map](https://az9713.github.io/ferroelectric-memory-to-ai/curriculum.html)
- [Publication inventory](https://az9713.github.io/ferroelectric-memory-to-ai/research/inventory.html)
- [Research-theme map](https://az9713.github.io/ferroelectric-memory-to-ai/research/themes.html)
- [Guided paper readings](https://az9713.github.io/ferroelectric-memory-to-ai/readings.html)
- [Searchable glossary](https://az9713.github.io/ferroelectric-memory-to-ai/glossary.html)

## Read the chapters

| Chapter | Web page |
|---|---|
| 1 | [Semiconductor foundations](https://az9713.github.io/ferroelectric-memory-to-ai/chapters/01-foundations.html) |
| 2 | [Materials, symmetry, and interfaces](https://az9713.github.io/ferroelectric-memory-to-ai/chapters/02-materials.html) |
| 3 | [Models and identifiability](https://az9713.github.io/ferroelectric-memory-to-ai/chapters/03-models.html) |
| 4 | [Programming, reading, and reliability](https://az9713.github.io/ferroelectric-memory-to-ai/chapters/04-devices.html) |
| 5 | [Circuits, sensing, and arrays](https://az9713.github.io/ferroelectric-memory-to-ai/chapters/05-arrays.html) |
| 6 | [Memory systems and reliability budgets](https://az9713.github.io/ferroelectric-memory-to-ai/chapters/06-memory.html) |
| 7 | [Digital implementation and Verilog](https://az9713.github.io/ferroelectric-memory-to-ai/chapters/07-rtl.html) |
| 8 | [Physical integration](https://az9713.github.io/ferroelectric-memory-to-ai/chapters/08-integration.html) |
| 9 | [AI workloads and memory placement](https://az9713.github.io/ferroelectric-memory-to-ai/chapters/09-workloads.html) |
| 10 | [Servers, racks, and useful work](https://az9713.github.io/ferroelectric-memory-to-ai/chapters/10-systems.html) |
| Capstone | [Defend a cross-stack claim](https://az9713.github.io/ferroelectric-memory-to-ai/chapters/11-capstone.html) |

## Projects and evidence

- [Run the cumulative Python projects](https://az9713.github.io/ferroelectric-memory-to-ai/projects/guide.html)
- [SPICE and process feasibility](https://az9713.github.io/ferroelectric-memory-to-ai/research/feasibility.html)
- [Engineering reproduction instructions](https://az9713.github.io/ferroelectric-memory-to-ai/hardware/README.html)
- [Scientific claim-to-source ledger](https://az9713.github.io/ferroelectric-memory-to-ai/research/source-ledger.html)
- [Researcher identity and coverage](https://az9713.github.io/ferroelectric-memory-to-ai/research/identity-and-coverage.html)
- [About, verification, and limitations](https://az9713.github.io/ferroelectric-memory-to-ai/about.html)

The bibliography covers **September 26, 2021–September 26, 2026**: 101 deduplicated scholarly records, including 14 selected full-text assessments and 87 metadata-only entries. Original publications are linked to their lawful sources; third-party PDFs and private production records are not included.

Python and circuit examples are explicitly labeled where synthetic or illustrative. RTL and generic synthesized-controller tests run; physical memory views remain abstract because compatible process support and characterized models were unavailable. This static website does not run a monitoring service or execute Python/SPICE/Verilog in the browser.

## Run locally

Clone the repository, open `index.html`, or serve it with `python -m http.server 8000`. MathJax is bundled, so equations do not depend on a CDN.

For Python calculations, use Python 3.13 and install `requirements.txt`. Then run:

```sh
python projects/polarization.py
python projects/stack.py all
python projects/capstone.py
```

SPICE requires ngspice. RTL simulation and synthesis require Icarus Verilog and Yosys; run `bash hardware/run-rtl.sh` from Linux, macOS, or WSL. See the engineering guide for the tested versions and model boundaries.

This is an independent educational resource, not an official Georgia Tech course or a product endorsement.
