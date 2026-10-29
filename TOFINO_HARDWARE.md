# ShapeShifter Deployment on Real Tofino 2 Hardware

## Clone ShapeShifter
```
cd ~
git clone https://github.com/zhudi217/conext26-paper15-artifacts.git
cd conext26-paper15-artifacts
```

## Compile and Launch ShapeShifter on the Tofino switch
```
bash p4_build.sh conext26-paper15-artifacts/p4/tofino_hardware/[sram/ss.p4 | tcam/ss_range.p4] P4_VERSION=p4_16 P4_ARCHITECTURE=t2na
./run_switchd.sh -p [ss | ss_range] --arch tf2
```

## Prepare an Experiment with Pretrained Models
Run the following command to prepare an experiment. The command converts a pretrained model into table entries and installs them into the data plane (if P4 SDE is present). The script also generates routing entries and pcap files for replaying. The ```--tcam``` specifies that the script targets the TCAM version of ShapeShifter.
```
python3 ss_prepare.py --target hardware --model [model_name] --dataset [dataset_name] [--tcam]
```
The generated files will be located in ```x/hardware/[model_name]/```. The script generates three files:
- [model_name]_[sram | tcam].pcap: A packet file containing packets with features.
- [model_name]_[sram | tcam].py: BFRT entries for the model.
- [model_name]_[sram | tcam]_forwarding.py: BFRT entries for forwarding.

## Run a Prepared Experiment and Parse the Results
Start packet captures on the receiver side:
```
sudo tcpdump -i [interface] -nn port 12345 -w [capture_filename].pcap
```
Copy the generated ```pcap``` file to the sender. Then, use tools such as ```tcpreplay``` to send the packets
```
sudo tcpreplay -i [interface] --loop=1 [model_name]_[sram | tcam].pcap
```
Finally, parse the result with ```recv_tofino_hardware.py```:
```
python3 recv_tofino_hardware.py --pcap [capture_filename].pcap --model [model_name] --dataset [dataset_name]
```
An example output looks like the following:
```
Y = original dataset labels; Y_swt = switch predictions; Y_serv = model predictions on the server.
Macro-F1 (Y_swt vs Y): 0.828177
Macro-F1 (Y_serv vs Y): 0.828177
Cohen's Kappa (Y_serv vs Y_swt): 1.000000
```

