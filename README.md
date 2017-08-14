# foqus
**FOQUS: Framework for Optimization and Quantification of Uncertainty and Sensitivity** 

Package includes: FOQUS GUI, Optimization Engine, Turbine Client. *Requires access to a Turbine Gateway installation either locally or on a separate cluster/server. #GAMS is required for heat integration option.*

## Development Practices

* Code development will be peformed in a forked copy of the repo. Commits will not be 
  made directly to the ngt-archive repo. Developers will submit a pull 
  request that is then merged by another team member, if another team member is available.
* Each pull request should contain only related modifications to a feature or bug fix.  
* Sensitive information (secret keys, usernames etc) and configuration data 
  (e.g database host port) should not be checked in to the repo.
* A practice of rebasing with the main repo should be used rather that merge commmits.

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

### Clone the repository

This repository used git submodules. The following foqus tools are
submodules to this project.

* [iREVEAL](https://github.com/CCSI-Toolset/iREVEAL)
* [turb_client](https://github.com/CCSI-Toolset/turb_client)
* [turb_hydro](https://github.com/CCSI-Toolset/turb_hydro)

Checkout out this repository and associated submodules

    $ git clone git@github.com:CCSI-Toolset/foqus.git
    $ git submodule update --init --recursive

Check the status of the submodules

    $ git submodule status
    ab70eabe6a0839fa2472ce4f65e07ab4fa93d788 foqus_lib/framework/surrogate/iREVEAL (2016.04.00-4-gab70eab)
    20091df823086c727057e0410abdc0cff90969c4 turb_client (2016.04.00-5-g20091df)
    60b8a7880bb2da864ab1fb8c4c965d05fb3f80a1 turb_hydro (2016.04.00-3-g60b8a78)

Build the distribution from cmd.exe

    $ make

## Build the Release

## Authors

* John Eslick

See also the list of [contributors](https://github.com/CCSI-Toolset/foqus/contributors) who participated in this project.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, 
see the [tags on this repository](https://github.com/CCSI-Toolset/foqus/tags). 

## License

See [LICENSE.md](LICENSE.md) file for details

## Copyright Notice

TBD
