"""
Created on: 06/07/2022 11:41

Author: Shyam Bhuller

Description: Reads a Trigger record and writes ADC and channels to file. Used in offline analysis of TPs
"""
import Utilities

import detdataformats.trigger_primitive
from hdf5libs import HDF5RawDataFile
import daqdataformats
import detchannelmaps

import argparse
import numpy as np
import h5py
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def TRDataFrame():
    """ Headers for DataFrame

    Returns:
        dictionary: headers
    """
    return {
        "adc" : [],
        "channel" : [],
        "timestamp" : [],
        "plane": [],
    }


def main(args):
    h5_file, cmap, toStudy = Utilities.OpenFile(args.file, args.records)
    
    #* collect run number
    with h5py.File(args.file, 'r') as h5py_file:
        run_number = h5py_file.attrs["run_number"]

    wibFrameSize = detdataformats.wib.WIBFrame.sizeof()
    print(f"wib frame size: {wibFrameSize}")

    #* crawl through records and store data
    WIBData = []
    for rid in toStudy:
        fragment_path = h5_file.get_fragment_dataset_paths(rid)[0] # get the path to the data
        fragment = h5_file.get_frag(fragment_path)
        Utilities.LogFragmentData(args.debug, fragment_path, fragment)
        n_frames = (fragment.get_size()-fragment.get_header().sizeof())//wibFrameSize # number of WIb frames is the  fragment data size / tp size
        if args.debug: print(f"number of WIB frames in fragment: {n_frames}")

        wibFrame = detdataformats.wib.WIBFrame(fragment.get_data()) # get frame (bit that has ADCs)
        wibHeader = wibFrame.get_wib_header() # get offline channel number from this
        wibTimestamp = wibFrame.get_timestamp()
        if args.debug: print(f"crate: {wibHeader.crate_no}, slot: {wibHeader.slot_no}, fibre: {wibHeader.fiber_no}")

        channels = [cmap.get_offline_channel_from_crate_slot_fiber_chan(wibHeader.crate_no, wibHeader.slot_no, wibHeader.fiber_no, c) for c in range(256)]
        plane = [cmap.get_plane_from_offline_channel(c) for c in channels]
        if args.debug: print(channels)

        #for each frame get the raw ADC and store this along with the corresponding channel
        for i in range(n_frames):
            frame = TRDataFrame() # create a blank data frame
            wib = detdataformats.wib.WIBFrame(fragment.get_data(i*wibFrameSize))
            
            frame["adc"].extend([wib.get_channel(c) for c in range(256)])
            frame["channel"].extend(channels)
            frame["plane"].extend(plane)
            frame["timestamp"].extend([wib.get_timestamp() for c in range(256)])
            WIBData.append(frame)
        adcs = [plane]
        rows = ["plane"]
        for i in range(n_frames):
            frame = TRDataFrame()
            wib = detdataformats.wib.WIBFrame(fragment.get_data(i*wibFrameSize))
            adcs.append([wib.get_channel(c) for c in range(256)])
            rows.append(wib.get_timestamp())
        df = pd.DataFrame(data=adcs, columns=channels, index=rows)
        mean = np.mean(adcs[1:])
        print(df)
        sns.heatmap(df[1:] - df[1:].mean(), cmap="seismic")
        plt.savefig(f"evd_tr_{args.records}.png", dpi=400)
        df.to_csv(f"tr_{args.records}.csv")
        
    #* convert to raw data waveform for LArSoft sumulation studies
    #? merge this with the above block to streamline converting and writing to file?
    # # get all channel ids
    # channels = []
    # for i in range(len(WIBData)):
    #     channels.extend(WIBData[i]["channel"])
    # print(f"total number of rows: {len(channels)}")
    
    # # get unique channels i.e. number of rows in output data
    # uniqueChannels = np.unique(channels)
    # print(f"number of unique channel numbers: {len(uniqueChannels)}")
    
    # totalSteps = len(uniqueChannels) + len(channels)
    # counter = 0
    # # add run number, channel and plane id to each row
    # adc = [[run_number, uniqueChannels[i], cmap.get_plane_from_offline_channel(uniqueChannels[i])] for i in range(len(uniqueChannels))]
    
    # # add ADCs from all records along each column
    # for i in range(len(uniqueChannels)):
    #     for j in range(len(WIBData)):
    #         index = WIBData[j]["channel"].index(uniqueChannels[i])
    #         adc[i].append(WIBData[j]["adc"][index])            
    #         counter += 1
    #         print(f"percentage converted: {(100 * counter / totalSteps):.2f}", end='\r')
    # data = np.array(adc)

    
    # quick preview
    # print(data)
    # if args.debug:
    #     with np.printoptions(threshold=5):
    #         print(data)
    
    # np.save(f"{args.outdir}{args.outfile}-{run_number}.npy", data) # save to file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to extract ADC values from a TR")
    parser.add_argument(dest="file", type=str, help="file to open.")
    parser.add_argument("-r", "--records", dest="records", type=str, default="0", help="trigger record/s to plot")
    parser.add_argument("-o", "--out-directory", dest="outdir", type=str, default="./", help="output file directory to store plots")
    parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="print record and TP information")
    parser.add_argument("-f", "--out-file", dest="outfile", type=str, default="test-waveform", help="output file name")
    args = parser.parse_args()
    main(args)
