# conext26-paper15-artifacts
Dear CoNEXT '26 AEC, thank you for evaluating our paper's artifacts. You will find the instructions to execute our artifact and reproduce the figures in our paper.

## Paper Results Reproduction
### Setup
We have prepared a configured VM for reproducing our experimental results. The VM can be downloaded here: [TODO]. Alternatively, the following dependencies are required to execute the experiments:
```
sudo apt install -y git
python3 -m pip install notebook numpy matplotlib pandas xgboost scikit-learn-intelex scikit-learn==1.7.1
```
Then clone ShapeShifter
```
git clone https://github.com/zhudi217/conext26-paper15-artifacts.git
```
The Jupyter notebooks are located in the ```test``` directory. Please execute them to reproduce the results.

## Deploying ShapeShifter on Intel Tofino 2
Instructions for deploying ShapeShifter with the Tofino model are here: [TOFINO_HARDWARE.md](TOFINO_HARDWARE.md).

## Deploying ShapeShifter with the Tofino Model
Instructions for deploying ShapeShifter with the Tofino model are here: [TOFINO_MODEL.md](TOFINO_MODEL.md).
