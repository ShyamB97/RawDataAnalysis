# RawDataAnalysis
analyse raw data (tp streams and trigger records)

DUNEDAQ envorinment:

dunedaq-v3.0.0 plus the additional branches in sourcecode:

detdataformats: 635affb

detchannelmaps: 4e9ba28

hdf5libs: 4177005

## setup environment:
You can follow dunedaq's [documentation](https://dune-daq-sw.readthedocs.io/en/latest/packages/daq-buildtools/), but the core things needed are `cvmfs` and `ptyhon 3` on the machine you are using.


Initialize spack (one time):
```bash
source `realpath /cvmfs/dunedaq.opensciencegrid.org/spack-externals/spack-installation/share/spack/setup-env.sh`
spack load python@3.8.3%gcc@8.2.0
```

Setup build tools:
```bash
source /cvmfs/dunedaq.opensciencegrid.org/setup_dunedaq.sh
setup_dbt dunedaq-v3.0.0 
```

Create work area:
```bash
dbt-create dunedaq-v3.0.0 <directory-name>
```

After some time the directory should be made. cd into the directory and in `sourcecode` clone the above repositories:
```bash
git clone https://github.com/DUNE-DAQ/detdataformats.git
cd detdataformats; git checkout 635affb; cd ..;
git clone https://github.com/DUNE-DAQ/detchannelmaps.git
cd detdataformats; git checkout bbebc27; cd ..;
git clone https://github.com/DUNE-DAQ/hdf5libs.git
cd hdf5libs; git checkout 4177005; cd ..;
```

Now source environment variables:
```bash
dbt-workarea-env
```

and now build:
```bash
dbt-build
```

Finally, add this repository in the top level directory:
```bash
git clone https://github.com/ShyamB97/RawDataAnalysis.git
```

Note, every time you want to run in the environment run the following from the work area:
```bash
source dbt-env.sh
dbt-workarea-env
```

To create ADC waveform data from a trigger record run the script `writeRawData.py`, example uasge to read the first trigger records 0-5:

```bash
python writeRawData.py <path-to-hdf5-file> -r "0-5" -d <output-file-directory> -f <file-name>
```