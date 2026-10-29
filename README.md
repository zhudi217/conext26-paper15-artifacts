# conext26-paper15-artifacts
Dear CoNEXT '26 AEC, thank you for evaluating our paper's artifacts. You will find the instructions to execute our artifact and reproduce the figures in our paper.

## Paper Results Reproduction
### Setup
We have prepared a configured VM for reproducing our experimental results. The VM can be downloaded here: [TODO]. Alternatively, the following dependencies are required to execute the experiments:
```
sudo apt install -y git jupyter-core
python3 -m pip install notebook numpy matplotlib pandas xgboost scikit-learn-intelex scikit-learn==1.7.1
```
Then clone ShapeShifter
```
git clone https://github.com/zhudi217/conext26-paper15-artifacts.git
```

### Experiment Execution
The Jupyter notebooks are located in the ```test``` directory. Please execute them to reproduce the results.

### Reconfiguration Test Experiment
If a real Tofino 2 switch is available, we provide a Python script to reconfigure models on the switch and measure the reconfiguration time. The script is located at ```conext26-paper15-artifacts/test/reconfiguration_test.py```. This script retrieves the IP address of the Tofino 2 switch from ```network.yaml```. To execute the script:
```
python test/reconfiguration_test.py --system SS          # SRAM. Results saved to test/reconfiguration/ss_s_ds1.csv
python test/reconfiguration_test.py --system SS_RANGE    # TCAM. Results saved to test/reconfiguration/ss_t_ds1.csv
python test/reconfiguration_test.py --system SS --reconfiguration-model differential        # Differential reconfiguration, SRAM. Results saved to test/reconfiguration/ss_s_d_ds1.csv
python test/reconfiguration_test.py --system SS_RANGE --reconfiguration-model differential        # Differential reconfiguration, TCAM. Results saved to test/reconfiguration/ss_t_d_ds1.csv
```

## Deploying ShapeShifter on Intel Tofino 2
Instructions for deploying ShapeShifter with the Tofino model are here: [TOFINO_HARDWARE.md](TOFINO_HARDWARE.md).

## Deploying ShapeShifter with the Tofino Model
Instructions for deploying ShapeShifter with the Tofino model are here: [TOFINO_MODEL.md](TOFINO_MODEL.md).
