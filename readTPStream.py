"""
Created on: 01/07/2022 12:33

Author: Shyam Bhuller

Description: Plots data from TP stream files from VD coldbox runs
"""
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

def LogFragmentData(debug, fragment_path, fragment):
    """ Log some fragment data

    Args:
        debug (bool): should we log
        fragment_path (str): fragment path
        fragment (daqdataformats.fragment): fragment
    """
    if debug:
        print(fragment_path)
        print(fragment)
        print(f"Inspecting {fragment_path}")
        print(f"Run number : {fragment.get_run_number()}")
        print(f"Trigger number : {fragment.get_trigger_number()}")
        print(f"Trigger TS    : {fragment.get_trigger_timestamp()}")
        print(f"Window begin  : {fragment.get_window_begin()}")
        print(f"Window end    : {fragment.get_window_end()}")
        print(f"Fragment type : {fragment.get_fragment_type()}")
        print(f"Fragment code : {fragment.get_fragment_type_code()}")
        print(f"Size          : {fragment.get_size()}")


def LogTPData(debug, tp):
    """ Log some tp data

    Args:
        debug (bool): should we log
        trigger primitive (daqdataformats.fragment): trigger primitive
    """
    if debug:
        print(f"version: {tp.version}")
        print(f"time_start: {tp.time_start}")
        print(f"time_peak: {tp.time_peak}")
        print(f"time_over_threshold: {tp.time_over_threshold}")
        print(f"channel: {tp.channel}")
        print(f"adc_integral: {tp.adc_integral}")
        print(f"adc_peak: {tp.adc_peak}")
        print(f"det_id: {tp.detid}")
        print(f"type: {tp.type}")
        print(f"algorithm: {tp.algorithm}")
        print(f"flag: {tp.flag}")
        print(f"size: {tp.sizeof()}")


def TPDataFrame() -> dict:
    """ Headers for DataFrame

    Returns:
        dictionary: headers
    """
    return {
        "time_start" : [],
        "time_peak" : [],
        "time_over_threshold" : [],
        "channel" : [],
        "adc_integral" : [],
        "adc_peak" : [],
        "det_id" : [],
        "plane" : [],
    }


def SortDataByPlane(data : pd.DataFrame) -> dict:
    """ Split data frame by which plane the channels correspond to.

    Args:
        data (pd.DataFrame): data which contains offline channel numbers

    Returns:
        dictionary: data frames corresponding to each plane
    """
    uPlane = data[data["plane"] == 0] # induction
    vPlane = data[data["plane"] == 1] # induction
    zPlane = data[data["plane"] == 2] # collection
    return {"u": uPlane, "v": vPlane, "z": zPlane}


def main(args):
    h5_file = HDF5RawDataFile(args.file)
    cmap = detchannelmaps.make_map('VDColdboxChannelMap') #? make channel map configurable?

    #* get attributes using h5py
    h5py_file = h5py.File(args.file, 'r')
    for attr in h5py_file.attrs.items():
        print("File Attribute ", attr[0], " = ", attr[1])

    records = h5_file.get_all_record_ids()
    print("Number of records: %d" % len(records))

    #? allow possiblity to select multiple time slices rather than one or all
    if(args.timeslice > -1):
        toStudy = [records[args.timeslice]]
    else:
        toStudy = records

    TPData = []
    for rid in toStudy:
        timeSlice = TPDataFrame() # create a blank data frame

        fragment_path = h5_file.get_fragment_dataset_paths(rid)[0] # get the path to the data
        fragment = h5_file.get_frag(fragment_path)
        LogFragmentData(args.debug, fragment_path, fragment)

        #* get number of TPs in fragment
        tp_size = detdataformats.trigger_primitive.TriggerPrimitive.sizeof() # get size of TP packet in bytes
        n_frames = (fragment.get_size()-fragment.get_header().sizeof())//tp_size # number of TP packets is the  fragment data size / tp size
        print(f"number of TPs in fragment: {n_frames}")

        #* iterate through each TP in the fragment and retrieve various information
        # TODO make code more efficient by plotting/binning data as TPs or fragments are parsed
        for i in range(n_frames):
            tp = detdataformats.trigger_primitive.TriggerPrimitive(fragment.get_data(i*tp_size)) # get TP data from pointer in fragment
            LogTPData(args.debug, tp)
            timeSlice["time_start"].append(tp.time_start)
            timeSlice["time_peak"].append(tp.time_peak)
            timeSlice["time_over_threshold"].append(tp.time_over_threshold)
            timeSlice["channel"].append(tp.channel)
            timeSlice["plane"].append(cmap.get_plane_from_offline_channel(tp.channel))
            timeSlice["adc_integral"].append(tp.adc_integral)
            timeSlice["adc_peak"].append(tp.adc_peak)
            timeSlice["det_id"].append(tp.detid)
        TPData.append(pd.DataFrame(timeSlice))

    # TODO decide whether plotting a gif of all Timeslices is worth it    
    def animate(i):
        im = plt.hist2d(TPData[i]["channel"], TPData[i]["time_peak"], bins=100)
        plt.xlabel("channel")
        plt.ylabel("peak time")
        plt.title(f"Time sice :{i}")
        return im

    if args.plot:
        os.makedirs(args.outdir, exist_ok=True)
    if args.plot == "gif":
        fig = plt.figure()
        ax = plt.axes()
        im = plt.hist2d(TPData[0]["channel"], TPData[0]["time_peak"], bins=100, norm=matplotlib.colors.LogNorm())
        plt.colorbar()
        anim = animation.FuncAnimation(fig, animate, frames=len(TPData))
        anim.save(f"{args.outdir}/anim.gif")

    if args.plot == "scatter" and args.timeslice > -1:
        planes = SortDataByPlane(TPData[0])

        for p in planes:
            plt.figure()
            plt.scatter(planes[p]["channel"], planes[p]["time_peak"], c=planes[p]["adc_integral"], s=5)
            cbar = plt.colorbar()
            cbar.set_label("ADC integral")
            plt.xlabel("channel")
            plt.ylabel("peak time")
            plt.title(f"Time sice :{records[args.timeslice]}, Plane : {p}")
            plt.tight_layout()
            plt.savefig(f"{args.outdir}/scatter_{p}.png", dpi=400)

    if args.plot == "validation":        
        data = pd.DataFrame(TPDataFrame())
        for d in TPData:
            data = pd.concat((data, d))

        for key in data:
            print(f"Plotting {key}")
            plt.figure()
            plt.hist(data[key], 40, histtype="step")
            plt.xlabel(key)
            plt.yscale("log")
            plt.tight_layout()
            plt.savefig(f"{args.outdir}/{key}.png")
            plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test script to plot some TPStream quantities")
    parser.add_argument(dest="file", type=str, help="file to open.")
    parser.add_argument("-o", "--out-directory", dest="outdir", type=str, default="plot", help="output file directory to store plots")
    parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="print record and TP information")
    parser.add_argument("-p", "--plot", dest="plot", choices=["validation", "gif", "scatter"], help="create plots of TP data")
    parser.add_argument("-t", "--timeslice", dest="timeslice", type=int, default=-1, help="timeslice number to plot")
    args = parser.parse_args()
    main(args)
