import Utilities

import trgdataformats

import argparse
import pandas as pd
import numpy as np
from rich import print

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

def main(args):
    h5_file, cmap, toStudy = Utilities.OpenFile(args.file, args.records, args.channelMap)

    fragments = {}
    for rid in toStudy:

        print(h5_file.get_fragment_dataset_paths(rid))
        for fp in h5_file.get_fragment_dataset_paths(rid):
            timeSlice = TPDataFrame() # create a blank data frame
            fragment = h5_file.get_frag(fp)
            header = fragment.get_header()
            Utilities.LogFragmentData(args.debug, fp, fragment)

            #* get number of TPs in fragment
            tp_size = trgdataformats.TriggerPrimitive.sizeof() # get size of TP packet in bytes
            n_frames = (fragment.get_size()-fragment.get_header().sizeof())//tp_size # number of TP packets is the  fragment data size / tp size
            # print(f"number of TPs in fragment: {n_frames}")

            #* iterate through each TP in the fragment and retrieve various information
            # TODO make code more efficient by plotting/binning data as TPs or fragments are parsed
            for i in range(n_frames):
                tp = trgdataformats.TriggerPrimitive(fragment.get_data(i*tp_size)) # get TP data from pointer in fragment
                LogTPData(args.debug, tp)
                timeSlice["time_start"].append(tp.time_start)
                timeSlice["time_peak"].append(tp.samples_to_peak)
                timeSlice["time_over_threshold"].append(tp.samples_over_threshold)
                timeSlice["channel"].append(tp.channel)
                try:
                    timeSlice["plane"].append(cmap.get_plane_from_offline_channel(tp.channel))
                except:
                    print(f"couldn't identify plane from offline channel {tp.channel}")
                    timeSlice["plane"].append(-1)
                timeSlice["adc_integral"].append(tp.adc_integral)
                timeSlice["adc_peak"].append(tp.adc_peak)
                timeSlice["det_id"].append(tp.detid)
            fragments[header.element_id.id] = pd.DataFrame(timeSlice)
        print(f"record id: {rid}")
        for k, v in fragments.items():
            print(f"TP input source ID: {k}")
            element_id = [cmap.get_element_name_from_offline_channel(c) for c in np.unique(v["channel"])]
            print(f"Element names: {np.unique(element_id)}")
        # for k2, v2 in v.items():
        #     print(f"{k2}, : {np.unique(v2)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test script to plot some TPStream quantities")
    parser.add_argument(dest="file", type=str, help="file to open.")
    parser.add_argument("-r", "--records", dest="records", type=str, default="0", help="trigger record/s to plot")
    parser.add_argument("-o", "--out-directory", dest="outdir", type=str, default="plot", help="output file directory to store plots")
    parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="print record and TP information")
    parser.add_argument("-p", "--plot", dest="plot", choices=["validation", "gif", "scatter"], help="create plots of TP data")
    parser.add_argument("-c", "--channel-map", dest="channelMap", choices=["VDColdboxChannelMap", "ProtoDUNESP1ChannelMap", "PD2HDChannelMap", "HDColdboxChannelMap", "PD2VDTPCChannelMap"], help="channel maps for ProtoDUNE")
    args = parser.parse_args()
    main(args)
