"""
Created on: 04/07/2022 09:58

Author: Shyam Bhuller

Description: Plots data from TP stream files from VD coldbox runs.
Works for daq runs prior to WIB ethernet readout.
"""
import Utilities

import fddetdataformats

import argparse
import matplotlib.pyplot as plt
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

def GetWibHeader(type, header):
    df = {
        "crate" : -1,
        "slot" : -1,
        "fiber": -1
    }
    if type  == "proto_wib":
        df["crate"] = header.crate_no
        df["slot"] = header.slot_no
        df["fiber"] = header.fiber_no
    elif type == "wib":
        df["crate"] = header.crate
        df["slot"] = header.slot
        df["fiber"] = header.link #? switch fiber to link?
    else:
        raise Exception("type must be proto_wib or wib, and must match the wib frame type")
    return df

def main(args):
    h5_file, cmap, toStudy = Utilities.OpenFile(args.file, args.records, args.channelMap)

    WIBData = []

    if args.frontend == "wib":
        wibFrame = fddetdataformats.WIB2Frame
    elif args.frontend == "proto_wib":
        wibFrame = fddetdataformats.WIBFrame
    else:
        raise Exception("front end type must be wib or proto_wib")

    wibFrameSize = wibFrame.sizeof()
    print(f"wib frame size: {wibFrameSize}")

    for rid in toStudy:
        trigger_record = TRDataFrame() # create a blank data frame

        fragment_path = h5_file.get_fragment_dataset_paths(rid)[0] # get the path to the data
        fragment = h5_file.get_frag(fragment_path)
        Utilities.LogFragmentData(args.debug, fragment_path, fragment)
        n_frames = (fragment.get_size()-fragment.get_header().sizeof())//wibFrameSize # number of WIb frames is the  fragment data size / tp size
        if args.debug: print(f"number of WIB frames in fragment: {n_frames}")

        frame = wibFrame(fragment.get_data())
        header = GetWibHeader(args.frontend, frame.get_header())

        if args.debug: print(f'crate: {header["crate"]}, slot: {header["slot"]}, fibre: {header["fiber"]}')
        channels = [cmap.get_offline_channel_from_crate_slot_fiber_chan(header["crate"], header["slot"], header["fiber"], c) for c in range(256)]
        planes = [cmap.get_plane_from_offline_channel(c) for c in channels]
        if args.debug: print(channels)

        for i in range(n_frames):
            wib = wibFrame(fragment.get_data(i*wibFrameSize))
            trigger_record["timestamp"].extend([wib.get_timestamp() for c in range(256)]) #-tr_ts
            if args.frontend == "proto_wib":
                trigger_record["adc"].extend([wib.get_channel(c) for c in range(256)])
            if args.frontend == "wib":
                trigger_record["adc"].extend([wib.get_adc(c) for c in range(256)])
            trigger_record["channel"].extend(channels)
            trigger_record["plane"].extend(planes)
        WIBData.append(trigger_record)

    x_range = [min(WIBData[0]["channel"]), max(WIBData[0]["channel"])]
    x_size = x_range[1]-x_range[0]+1
    x = np.linspace(x_range[0], x_range[1], x_size)

    y_range = [min(WIBData[0]["timestamp"]), max(WIBData[0]["timestamp"])]
    y_size = y_range[1]-y_range[0]+1
    y = np.linspace(y_range[0], y_range[1], y_size)

    print((x_size, y_size))

    grid = np.meshgrid(x, y)
    adcmap = np.array(WIBData[0]["adc"])
    adcmap.reshape((y_size-1, x_size-1))
    #print(adcmap)

    plt.pcolor(WIBData[0]["channel"], WIBData[0]["timestamp"], WIBData[0]["adc"], bins=100)
    plt.savefig(f"test.png", dpi=400)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test script to plot some TPStream quantities")
    parser.add_argument(dest="file", type=str, help="file to open.")
    parser.add_argument("-r", "--records", dest="records", type=str, default="0", help="trigger record/s to plot")
    parser.add_argument("-o", "--out-directory", dest="outdir", type=str, default="plot", help="output file directory to store plots")
    parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="print record and TP information")
    parser.add_argument("-p", "--plot", dest="plot", choices=["validation", "gif", "scatter"], help="create plots of TP data")
    parser.add_argument("-f", "--frontend", dest="frontend", choices=["proto_wib", "wib"], default="proto_wib", help="front end type")
    parser.add_argument("-c", "--channel-map", dest="channelMap", choices=["VDColdboxChannelMap", "ProtoDUNESP1ChannelMap", "PD2HDChannelMap", "HDColdboxChannelMap"], help="channel maps for ProtoDUNE")
    args = parser.parse_args()
    main(args)
