# RawDataAnalysis
analyse raw data (tp streams and trigger records)

DUNEDAQ envorinment:

dunedaq-v5.3.x

## setup environment:
You can follow dunedaq's [documentation](https://dune-daq-sw.readthedocs.io/en/latest/packages/daq-buildtools/), but the core things needed are `cvmfs` and `ptyhon 3` on the machine you are using.


Installtion:
```bash
source /cvmfs/dunedaq.opensciencegrid.org/setup_dunedaq.sh
setup_dbt latest
dbt-create release fddaq-v5.3.1-a9 # directory name optional
cd fddaq-v5.3.1-a9
source env.sh
dbt-workarea-env
dbt-build
pip install seaborn
mkdir work
cd work
git clone https://github.com/ShyamB97/RawDataAnalysis.git
```

Note, every time you want to run in the environment run the following from the work area:
```bash
source env.sh
```

To create ADC waveform data from a trigger record run the script `writeRawData.py`, example uasge to read the first trigger records 0-5:

```bash
python writeRawData.py <path-to-hdf5-file> -r "0-5" -o <output-file-directory> -f <file-name>
```