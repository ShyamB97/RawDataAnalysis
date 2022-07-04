"""
Created on: 04/07/2022 09:58

Author: Shyam Bhuller

Description: Plots data from TP stream files from VD coldbox runs
"""
import Utilities

import detdataformats.trigger_primitive
from hdf5libs import HDF5RawDataFile
import daqdataformats
import detchannelmaps

import os
import argparse
import h5py
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import numpy as np

def TRDataFrame():
    """ Headers for DataFrame

    Returns:
        dictionary: headers
    """
    return {
        "timestamp" : [],
        "adc" : [],
        "channel" : [],
        "plane" : [],
    }


def main(args):
    h5_file, cmap, toStudy = Utilities.OpenFile(args.file, args.records)
    
    WIBData = []
    wibFrameSize = detdataformats.wib.WIBFrame.sizeof()
    print(f"wib frame size: {wibFrameSize}")

    for rid in toStudy:
        trigger_record = TRDataFrame() # create a blank data frame

        fragment_path = h5_file.get_fragment_dataset_paths(rid)[0] # get the path to the data
        fragment = h5_file.get_frag(fragment_path)
        Utilities.LogFragmentData(args.debug, fragment_path, fragment)
        n_frames = (fragment.get_size()-fragment.get_header().sizeof())//wibFrameSize # number of WIb frames is the  fragment data size / tp size
        if args.debug: print(f"number of WIB frames in fragment: {n_frames}")

        wibFrame = detdataformats.wib.WIBFrame(fragment.get_data())
        wibHeader = wibFrame.get_wib_header()
        if args.debug: print(f"crate: {wibHeader.crate_no}, slot: {wibHeader.slot_no}, fibre: {wibHeader.fiber_no}")
        channels = [cmap.get_offline_channel_from_crate_slot_fiber_chan(wibHeader.crate_no, wibHeader.slot_no, wibHeader.fiber_no, c) for c in range(256)]
        planes = [cmap.get_plane_from_offline_channel(c) for c in channels]
        if args.debug: print(channels)

        for i in range(n_frames):
            wib = detdataformats.wib.WIBFrame(fragment.get_data(i*wibFrameSize))
            trigger_record["timestamp"].extend([wib.get_timestamp() for c in range(256)]) #-tr_ts
            trigger_record["adc"].extend([wib.get_channel(c) for c in range(256)])
            trigger_record["channel"].extend(channels)
            trigger_record["plane"].extend(planes)
        WIBData.append(trigger_record)

    x_range = [min(WIBData[0]["channel"]), max(WIBData[0]["channel"])]
    x_size = x_range[1]-x_range[0]+1
    x = np.linspace(x_range[0], x_range[1], x_size)

    y_range = [min(WIBData[0]["timestamp"]), max(WIBData[0]["timestamp"])]
    y_size = y_range[1]-y_range[0]+1
    y = np.linspace(y_range[0], y_range[1], y_size)

    grid = np.meshgrid(x, y)
    adcmap = np.array(WIBData[0]["adc"])
    adcmap.reshape((y_size-1, x_size-1))
    print(adcmap)

    #plt.pcolor(WIBData[0]["channel"], WIBData[0]["timestamp"], WIBData[0]["adc"], bins=100)
    #plt.savefig(f"test.png", dpi=400)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test script to plot some TPStream quantities")
    parser.add_argument(dest="file", type=str, help="file to open.")
    parser.add_argument("-o", "--out-directory", dest="outdir", type=str, default="plot", help="output file directory to store plots")
    parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="print record and TP information")
    parser.add_argument("-p", "--plot", dest="plot", choices=["validation", "gif", "scatter"], help="create plots of TP data")
    parser.add_argument("-t", "--trigger-record", dest="records", type=int, default=-1, help="trigger record to plot")
    args = parser.parse_args()
    main(args)
