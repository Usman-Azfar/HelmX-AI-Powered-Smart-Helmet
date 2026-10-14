# Dataset and derived-artifact licensing

The MIT license covers original HelmX software and documentation. It does not replace upstream licenses or establish redistribution rights for datasets, model weights, or derived caches.

| Material | Recorded source and license status | Deposit disposition |
|---|---|---|
| `data/darus` | Repository records identify CC BY 4.0 and DOI https://doi.org/10.18419/darus-3301; attribution must be retained and current source terms verified before redistribution. | Local input only in this source release; no MIT relicensing. |
| `data/fall`, `data/near-fall` | Dataset on powered two-wheelers fall and critical events detection, https://doi.org/10.1016/j.dib.2019.103828. Dataset redistribution terms have not been independently established. Article licensing alone is insufficient evidence of file licensing. | Local input only; public redistribution pending source terms. |
| `data/carla`, `data/road` | Records describe simulator-generated and in-house recordings. Ownership/participant redistribution disposition is not documented. | Local input only pending ownership/redistribution confirmation. |
| `data/extended_normal_road_raw`, `data/external_scooter_riding_raw`, `data/external_simra_bicycle_raw` | External evaluation sources with source-specific attribution and use conditions recorded alongside the local data. | Local evaluation input only in this source release; obtain from the original sources. |
| Model weights and fitted normalizers | Derived from the recorded training sources. | Excluded from the public source release until redistribution rights are confirmed; no weight license is asserted. |
| New Pi measurements | Recorded by this campaign; no public-data license assigned in this software-license update. | Retained in the local evidence package. |

Author supplied on 7 October 2026: Usman Azfar, PUCIT, University of the Punjab. The author authorized choosing a license; MIT was selected for original software. No DOI, release, public upload, or upstream permissions are implied by these local files.

The repository's `.gitignore` enforces this conservative publication policy. See
`data/README.md` for the local directory layout and the reproducibility manifest
under `results/reproducibility/` for hashes of the exact files used in reported runs.
