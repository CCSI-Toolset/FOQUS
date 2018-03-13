# FOQUS: Framework for Optimization and Quantification of Uncertainty and Sensitivity

Package includes: FOQUS GUI, Optimization Engine, Turbine Client. *Requires access to a Turbine Gateway installation either locally or on a separate cluster/server. #GAMS is required for heat integration option.*

## Getting Started

### Pre-requisties
The build/dev environment must have the following tools installed. It has been
tested with the following versions. Use other versions at your own risk

+ Apache Ant
+ Coin Library
+ Git for Windows
+ Java 1.8
+ Microsoft Visual Studio 11.0
+ Microsoft .NET v4.0.30319
+ Python 2.7
+ TexLive for Windows
+ Wix Toolset v3.10

### Install
See the [installation](INSTALLmd.) instructions for details.

### FAQ
See our [FAQ][FAQ.md] for frequently asked questions and answers

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
[releases](../../releases) or [tags](../..//tags) on this repository.

## License & Copyright
See [LICENSE.md](LICENSE.md) file for details
