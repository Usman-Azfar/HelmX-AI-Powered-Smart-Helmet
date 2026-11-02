# Licensing and redistribution map

This mixed reproducibility package contains software, documentation, trained
model artifacts, author-generated Raspberry Pi evidence, and summaries derived
from separately obtained source datasets. One license must not be inferred for
every file.

## Original HelmX software and documentation — MIT

Original source code, scripts, tests, configuration templates, and project
documentation are licensed under the MIT License in `LICENSE`.

## Raspberry Pi evidence — CC BY 4.0

Author-generated experimental evidence and result artifacts under `piResults/`
are licensed under the Creative Commons Attribution 4.0 International license
(SPDX: `CC-BY-4.0`), except for third-party names or materials explicitly
identified in provenance records.

License text and terms: https://creativecommons.org/licenses/by/4.0/legalcode

Recommended attribution:

> Usman Azfar, HelmX Raspberry Pi deployment-validation
> evidence, version 1.1.0, 2026.

## Trained model and fitted-normalizer artifacts

The authors confirm that the included `.keras`, `.tflite`, and fitted model
normalization `.npz` artifacts are author-generated derivative/model artifacts
that they have permission to redistribute publicly. They are provided in this
archive for research, verification, and reproducibility. Copyright remains with
the authors; no ownership of or license to the underlying third-party source
datasets is conveyed. Cite this release and the upstream datasets when using
these artifacts.

These model artifacts are distributed in the Zenodo reproducibility archive
(https://doi.org/10.5281/zenodo.23770989) and are not tracked in this Git
branch.

This redistribution notice applies to the trained/fitted files under `models/`
and their byte-identical validation copies. Other `.npz` files under
`piResults/` are covered by CC BY 4.0 as author-generated evidence.

## Offline results and figures

Author-created summaries, metrics, and figures under `results/` are released
with the project documentation under MIT unless a file's embedded attribution
states otherwise. Numerical facts do not convey rights in the source datasets.

## Third-party datasets

Third-party source datasets are not included and are not relicensed. CARLA,
DaRUS, Boubezoul (fall and near-fall), STRIDE (the `data/road/` training
sessions and the within-source extended evaluation), scooter (CC BY 4.0),
SimRa (CC BY-NC 4.0, non-commercial), and any other upstream material remain
subject to their original terms; see `THIRD_PARTY_SOURCE_MAP.csv`. `DATA_LICENSES.md`, `data/README.md`, result
provenance, and the reproducibility manifest provide citations, hashes, and
download/reconstruction instructions without redistributing source data.

## Author authorization

On 2026-10-15, the author confirmed permission to publicly redistribute the
included trained/fitted model artifacts and authorized CC BY 4.0 for the
author-generated Raspberry Pi evidence. Original software and documentation
remain under MIT.

