# FOQUS: Framework for Optimization, Quantification of Uncertainty, and Surrogates
Package includes: FOQUS GUI, Optimization Engine, Turbine Client. *Requires access to a Turbine Gateway installation either locally or on a separate cluster/server. #GAMS is required for heat integration option.*

## Project Status
<!-- BEGIN Status badges -->
[![Documentation Status](https://readthedocs.org/projects/foqus/badge/?version=latest)](https://foqus.readthedocs.io/en/latest/?badge=latest)
[![Tests](https://github.com/CCSI-Toolset/FOQUS/actions/workflows/tests.yml/badge.svg)](https://github.com/CCSI-Toolset/FOQUS/actions/workflows/tests.yml)
[![Nightlies](https://github.com/CCSI-Toolset/FOQUS/actions/workflows/nightlies.yml/badge.svg)](https://github.com/CCSI-Toolset/FOQUS/actions/workflows/nightlies.yml)
[![GitHub contributors](https://img.shields.io/github/contributors/CCSI-Toolset/FOQUS.svg)](https://github.com/CCSI-Toolset/FOQUS/graphs/contributors)
[![Merged PRs](https://img.shields.io/github/issues-pr-closed-raw/CCSI-Toolset/FOQUS.svg?label=merged+PRs)](https://github.com/CCSI-Toolset/FOQUS/pulls?q=is:pr+is:merged)
[![Issue stats](http://isitmaintained.com/badge/resolution/CCSI-Toolset/FOQUS.svg)](http://isitmaintained.com/project/CCSI-Toolset/FOQUS)
[![Downloads](https://pepy.tech/badge/ccsi-foqus)](https://pepy.tech/project/ccsi-foqus)
<!-- End Status badges -->

## Getting Started

### Install
To get started right away, start with the [installation](https://foqus.readthedocs.io/en/stable/chapt_install/index.html) instructions for the most recent stable release.

We have several videos playlists on how to install FOQUS:
* [Python 3 version of FOQUS](https://www.youtube.com/playlist?list=PLmBxveOxgaXl-H9Wp3X6SIpVWg3Ua1Y2X)
* [Optional software for FOQUS](https://www.youtube.com/playlist?list=PLmBxveOxgaXn24WEhFMyrtA-0_4Rvlesw)
* [Python 2 version of FOQUS](https://www.youtube.com/playlist?list=PLmBxveOxgaXkyrQP9CAgUu_ZPYsS4qCvd) 

### Documentation and User's Manual
Read the full [documentation for FOQUS](https://foqus.readthedocs.io/en/stable/) (including the installation manual).  Documentation for [past releases or the latest](https://readthedocs.org/projects/foqus/) (unreleased) development version are available.

A complete set of usage and installation instruction videos for FOQUS are available on our [YouTube channel](https://www.youtube.com/channel/UCBVjFnxrsWpNlcnDvh0_GzQ/).

### FAQ
See our [FAQ](FAQs.md) for frequently asked questions and answers

## Authors
See also the list of [contributors](../../graphs/contributors) who participated in this project.

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
See [LICENSE.md](LICENSE.md) file for details.

## Reference
If you are using FOQUS for your work, please reference the following paper:

Miller, D.C., Agarwal, D., Bhattacharyya, D., Boverhof, J., Chen, Y., Eslick, J., Leek, J., Ma, J., Mahapatra, P., Ng, B., Sahinidis, N.V., Tong, C., Zitney, S.E., 2017. Innovative computational tools and models for the design, optimization and control of carbon capture processes, in: Papadopoulos, A.I., Seferlis, P. (Eds.), Process Systems and Materials for CO2 Capture: Modelling, Design, Control and Integration. John Wiley & Sons Ltd, Chichester, UK, pp. 311–342.

## Technical Support
If you require assistance, or have questions regarding FOQUS, please send an e-mail to: ccsi-support@acceleratecarboncapture.org or [open an issue in GitHub](https://github.com/CCSI-Toolset/FOQUS/issues)
