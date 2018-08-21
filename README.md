
| CI Build | Status |
|:---|:---:|
| Jenkins Manual | [![Build Status](https://keeling.lbl.gov/buildStatus/icon?job=foqus-docs)](https://keeling.lbl.gov/job/foqus-docs) |

# FOQUS: Framework for Optimization, Quantification of Uncertainty, and Surrogates

Package includes: FOQUS GUI, Optimization Engine, Turbine Client. *Requires access to a Turbine Gateway installation either locally or on a separate cluster/server. #GAMS is required for heat integration option.*

## Getting Started

### Install
See the [installation](INSTALL.md) instructions for details.

### FAQ
See our [FAQ](FAQs.md) for frequently asked questions and answers

## Authors
See also the list of [contributors](../contributors) who participated in this project.

## Development Practices
* Code development will be peformed in a forked copy of the repo. Commits will not be 
  made directly to the repo. Developers will submit a pull request that is then merged
  by another team member, if another team member is available.
* Each pull request should contain only related modifications to a feature or bug fix.  
* Sensitive information (secret keys, usernames etc) and configuration data 
  (e.g database host port) should not be checked in to the repo.
* A practice of rebasing with the main repo should be used rather that merge commmits.

## Versioning
We use [SemVer](http://semver.org/) for versioning. For the versions available, 
[releases](../../releases) or [tags](../../tags) on this repository.

## License & Copyright
See [LICENSE.md](LICENSE.md) file for details

## Reference
If you are using FOQUS for your work, please reference the following paper:

Miller, D.C., Agarwal, D., Bhattacharyya, D., Boverhof, J., Chen, Y., Eslick, J., Leek, J., Ma, J., Mahapatra, P., Ng, B., Sahinidis, N.V., Tong, C., Zitney, S.E., 2017. Innovative computational tools and models for the design, optimization and control of carbon capture processes, in: Papadopoulos, A.I., Seferlis, P. (Eds.), Process Systems and Materials for CO2 Capture: Modelling, Design, Control and Integration. John Wiley & Sons Ltd, Chichester, UK, pp. 311–342.
