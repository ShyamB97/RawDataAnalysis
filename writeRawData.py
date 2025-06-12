"""
Created on: 06/07/2022 11:41

Author: Shyam Bhuller

Description: Reads a Trigger record and writes ADC and channels to file. Used in offline analysis of TPs
"""
import Utilities
import fddetdataformats
import rawdatautils

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
    h5_file, cmap, toStudy = Utilities.OpenFile(args.file, args.records, args.channel_map)
    
    #* collect run number
    with h5py.File(args.file, 'r') as h5py_file:
        run_number = h5py_file.attrs["run_number"]

    wibFrameSize = fddetdataformats.WIBEthFrame.sizeof()
    print(f"wib frame size: {wibFrameSize}")

    #* crawl through records and store data
    WIBData = []
    for rid in toStudy:
        fragment_path = h5_file.get_fragment_dataset_paths(rid)[0] # get the path to the data
        fragment = h5_file.get_frag(fragment_path)
        Utilities.LogFragmentData(args.debug, fragment_path, fragment)
        n_frames = (fragment.get_size()-fragment.get_header().sizeof())//wibFrameSize # number of WIb frames is the  fragment data size / tp size
        if args.debug: print(f"number of WIB frames in fragment: {n_frames}")

        wibFrame = fddetdataformats.WIBEthFrame(fragment.get_data()) # get frame (bit that has ADCs)
        wibHeader = wibFrame.get_daqheader() # get offline channel number from this
        wibTimestamp = wibFrame.get_timestamp()
        if args.debug: print(f"crate: {wibHeader.crate_no}, slot: {wibHeader.slot_no}, fibre: {wibHeader.fiber_no}")

        channels = [cmap.get_offline_channel_from_det_crate_slot_stream_chan(wibHeader.det_id, wibHeader.crate_id, wibHeader.slot_id, wibHeader.stream_id, c) for c in range(64)]
        plane = [cmap.get_plane_from_offline_channel(c) for c in channels]
        adc = rawdatautils.unpack.wibeth.np_array_adc(fragment)
        timestamps = rawdatautils.unpack.wibeth.np_array_timestamp(fragment)
        if args.debug: print(channels)

        df = pd.DataFrame(data=np.vstack([plane, adc]), columns=channels, index=["plane", *timestamps])
        print(df.head(n=5))
        plt.figure()
        sns.heatmap(df[1:] - df[1:].mean(), cmap="seismic")
        plt.savefig(f"evd_tr_{rid[0]}.png", dpi=400)
        df.to_csv(f"tr_{rid[0]}.csv")
        
    #* convert to raw data waveform for LArSoft sumulation studies
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
    parser.add_argument("-c", "--channel-map", dest="channel_map", choices=["VDColdboxChannelMap", "ProtoDUNESP1ChannelMap", "PD2HDChannelMap", "HDColdboxChannelMap", "PD2VDTPCChannelMap"], help="channel maps for ProtoDUNE")
    args = parser.parse_args()
    main(args)
