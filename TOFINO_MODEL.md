# Running ShapeShifter with Intel Tofino Model
The following instructions tell you how to install the necessary environments to run ShapeShifter with Intel Tofino model.

## Recommended Setup
- Ubuntu 22.04 with x86-64 architecture (required)
- Memory: 8GB
- Disk: 50 GB
- ```sudo``` access (required).
- Python >= 3.10

## Install Software Dependencies
```
sudo apt install -y git
```
## Clone Necessary Repositories
### Clone the Open-P4Studio from GitHub
```
git clone https://github.com/p4lang/open-p4studio.git
cd open-p4studio
git submodule update --init --recursive
```

### Clone ShapeShifter
```
cd ~
git clone https://github.com/zhudi217/conext26-paper15-artifacts.git
```

## Build and Install Intel® P4 Studio Software Development Environment (SDE)
### Copy SDE Configuration
```
cp ~/conext26-paper15-artifacts/tofino2_ss.yaml ~/open-p4studio/p4studio/profiles/tofino2_ss.yaml
```

### Install the SDE
In the ```open-p4studio``` directory, run
```
./p4studio/p4studio profile apply ./p4studio/profiles/tofino2_ss.yaml
```
This command will check system compatibility and install necessary dependencies for the SDE. The installation will take about 60 minutes.

### Add SDE to PATH
```
./create-setup-script.sh > ~/setup-open-p4studio.bash
source ~/setup-open-p4studio.bash
```

## Deploy and Run ShapeShifter
### Install Dependencies
```
python3 -m pip install scapy joblib numpy xgboost scikit-learn==1.7.1
```

### Compile the Data Plane Program
Open a new terminal, ```terminal1```, and compile ShapeShifter's data plane program. We use the SRAM version as an exmaple.
```
% Execute the following commands in terminal1
cd ~/open-p4studio/
source ~/setup-open-p4studio.bash

rm -rf   $SDE/build/p4-build/my_program
mkdir -p $SDE/build/p4-build/ss
cd $SDE/build/p4-build/shapeshifter

cmake $SDE/p4studio                                         \
     -DCMAKE_MODULE_PATH="$SDE/cmake"                       \
     -DCMAKE_INSTALL_PREFIX="$SDE_INSTALL"                  \
     -DP4C=$SDE_INSTALL/bin/p4c                             \
     -DP4_PATH="$HOME/conext26-paper15-artifacts/p4/tofino_model/sram/ss.p4"   \
     -DP4_NAME=ss                                           \
     -DP4_LANG=p4_16                                        \
     -DTOFINO=OFF -DTOFINO2=ON

make [VERBOSE=1] -j install
```

Still in ```terminal1```, set up the virtual network interfaces.
```
cd $SDE
sudo ${SDE_INSTALL}/bin/veth_setup.sh 128
```
and then run the following command to start the Tofino model
```
./run_tofino_model.sh -p ss --arch tofino2
```

Now, open a new terminal, ```terminal2```, and launch the driver:
```
cd ~/open-p4studio/
source ~/setup-open-p4studio.bash
./run_switchd.sh -p ss --arch tofino2
```

### Prepare an Experiment with Pretrained Models
Open a new terminal, ```terminal3``` and run the following command. The command converts a pretrained model into table entries and install them into the data plane.
```
cd ~/open-p4studio
source ~/setup-open-p4studio.bash

cd ~/conext26-paper15-artifacts
python3 ss_prepare.py --target model --dataset ciciot22 --model ss_dt_ds2
```
To run with a different model, put the pretrained model under ```models``` directory.

### Run an Prepared Experiment and Parse the Results
To run the experiment, we will use ```terminal3``` as the sender and a new terminal, ```terminal4``` to receive packets. First, set up the receiver in ```terminal4```.
```
cd ~/conext26-paper15-artifacts
sudo python3 recv_tofino_model.py --model ss_dt_ds2 --dataset ciciot22
```

Then we can start sending packets in ```terminal3```
```
sudo python3 send_tofino_model.py --pcap [pcap_path]
```
The results will be printed out in ```terminal4```. An example output looks like the following:
```
Y = original dataset labels; Y_swt = switch predictions; Y_serv = model predictions on the server.
Macro-F1 (Y_swt vs Y): 0.828177
Macro-F1 (Y_serv vs Y): 0.828177
Cohen's Kappa (Y_serv vs Y_swt): 1.000000
```

### Model Reconfiguration
To reconfigure the data plane, simply run the experiment preparation commands again with a new model in ```terminal3```:
```
python3 ss_prepare.py --target model --dataset ciciot22 --model ss_rf_ds2
```
