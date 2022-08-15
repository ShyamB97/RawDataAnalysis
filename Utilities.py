"""
Created on: 04/07/2022 11:44

Author: Shyam Bhuller

Description: Utility functions
"""

import detdataformats.trigger_primitive
from hdf5libs import HDF5RawDataFile
import daqdataformats
import detchannelmaps

import pandas as pd
import h5py
import re

def OpenFile(filename : str, recordsToStudy : str, channelMap : str = 'VDColdboxChannelMap'):
    """Open file and get a list of records/slices to process and the channel map.

    Args:
        filename (str): hdf5file
        recordsToStudy (str): record mask

    Returns:
        tuple: data file class, channel map, record list
    """
    h5_file = HDF5RawDataFile(filename)
    cmap = detchannelmaps.make_map(channelMap) #? make channel map configurable? yes.

    #* get attributes using h5py
    h5py_file = h5py.File(filename, 'r')
    for attr in h5py_file.attrs.items():
        print("File Attribute ", attr[0], " = ", attr[1])

    records = h5_file.get_all_record_ids()
    print("Number of records: %d" % len(records))
    selectedRecords = ParseRecordMap(recordsToStudy)
    toStudy = [records[selectedRecords[i]] for i in range(len(selectedRecords))]

    return h5_file, cmap, toStudy


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


def ParseRecordMap(string : str):
    """ Break down a record map into a list of records to study

    Args:
        string (str): record map

    Returns:
        list: list of record numbers
    """
    records = []
    if not re.search("[a-zA-Z]", string):
        strs = string.split(",")
        for s in strs:
            r = list(map(int, s.split("-")))
            if len(r) == 1:
                records.extend(r)
            else:
                records.extend(range(r[0], r[-1]+1))
    print(records)
    return records
