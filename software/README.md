# Running ShapeShifter with Intel Tofino Model
The following instructions tell you how to install the necessary environments to run ShapeShifter with Intel Tofino model.

## Recommended Setup
- Ubuntu 22.04 with x86-64 architecture (required)
- Memory: 8GB
- Disk: 50 GB
- ```sudo``` access (required).

## Install Software Dependencies
```
sudo apt install -y git
```

## Build and Install Intel® P4 Studio Software Development Environment (SDE)
### Clone the SDE from GitHub
```
git clone https://github.com/p4lang/open-p4studio.git
cd open-p4studio
git submodule update --init --recursive
```

### Install the SDE
In the ```open-p4studio``` directory, run
```
./p4studio/p4studio profile apply ./p4studio/profiles/testing.yaml
```
This command will check system compatibility and install necessary dependencies for the SDE.

## Deploy and Run ShapeShifter
### Clone Shapeshifter from GitHub
Clone the code, scripts and preprocessed dataset of Shapeshifter with the following commands
```
cd ~
git clone https://github.com/zhudi217/conext26-paper15-artifacts.git
cd conext26-paper15-artifacts/software
```

### Prepare an Experiment with Pretrained Models

### Run an Prepared Experiment
Running the experiment requires opening multiple terminals. The following commands use ```terminal[index]``` to indicate in which terminal to run a command.