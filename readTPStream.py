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

def TPDict():
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

def main(args):
    h5_file = HDF5RawDataFile(args.file)
    cmap = detchannelmaps.make_map('VDColdboxChannelMap')
    # get attributes using h5py
    # this is a bit messy at the moment: should try to combine interfaces here
    h5py_file = h5py.File(args.file, 'r')
    for attr in h5py_file.attrs.items():
        print("File Attribute ", attr[0], " = ", attr[1])

    records = h5_file.get_all_record_ids()
    print("Number of records: %d" % len(records))

    if(args.timeslice > -1):
        toStudy = [records[args.timeslice]]
    else:
        toStudy = records
    
    TPData = []
    for rid in toStudy:

        timeSlice = TPDict()
        fragment_path = h5_file.get_fragment_dataset_paths(rid)[0]
        fragment = h5_file.get_frag(fragment_path)
        if args.debug:
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
        tp_size = detdataformats.trigger_primitive.TriggerPrimitive.sizeof()
        n_frames = (fragment.get_size()-fragment.get_header().sizeof())//tp_size
        print(f"number of TPs in fragment: {n_frames}")
        for i in range(n_frames):
            tp = detdataformats.trigger_primitive.TriggerPrimitive(fragment.get_data(i*tp_size))
            if args.debug:
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
            timeSlice["time_start"].append(tp.time_start)
            timeSlice["time_peak"].append(tp.time_peak)
            timeSlice["time_over_threshold"].append(tp.time_over_threshold)
            timeSlice["channel"].append(tp.channel)
            #* try figure out which plane the channel corresponds to
            #print(f"channel {tp.channel} : {cmap.get_plane_from_offline_channel(tp.channel)}")
            timeSlice["plane"].append(cmap.get_plane_from_offline_channel(tp.channel))
            timeSlice["adc_integral"].append(tp.adc_integral)
            timeSlice["adc_peak"].append(tp.adc_peak)
            timeSlice["det_id"].append(tp.detid)
        TPData.append(timeSlice)
    
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
        plt.scatter(TPData[0]["channel"], TPData[0]["time_peak"], c=TPData[0]["adc_peak"], s=5)
        cbar = plt.colorbar()
        cbar.set_label("peak adc")
        plt.xlabel("channel")
        plt.ylabel("peak time")
        plt.title(f"Time sice :{records[args.timeslice]}")
        plt.tight_layout()
        plt.savefig(f"{args.outdir}/scatter.png", dpi=400)

    if args.plot == "validation":
        
        data = TPDict()
        for d in TPData:
            for key in d:
                data[key] += d[key]

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
