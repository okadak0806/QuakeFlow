# %%
import argparse
import json
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from pathlib import Path
from typing import Dict, List

import fsspec
import pandas as pd
from tqdm import tqdm


# %%
def parse_fname(mseed, region):
    if region == "SC":
        fname = mseed.split("/")[-1]  #
        network = fname[:2]
        station = fname[2:7].rstrip("_")
        instrument = fname[7:9]
        component = fname[9]
        location = fname[10:12].rstrip("_")
        year = fname[13:17]
        jday = fname[17:20]
        station_id = f"{station}.{network}.{location}.{instrument}"
    elif region == "NC":
        fname = mseed.split("/")[-1].split(".")
        station = fname[0]
        network = fname[1]
        instrument = fname[2][:-1]
        component = fname[2][-1]
        location = fname[3]
        assert fname[4] == "D"
        year = fname[5]
        jday = fname[6]

    return station_id, network, station, location, instrument, component, year, jday


def collect_mseeds(
    root_path: str,
    region: str,
    year=2023,
    node_rank: int = 0,
    num_nodes: int = 1,
    protocol: str = "s3",
    bucket: str = "",
    token: Dict = None,
) -> int:

    # %%
    fs_result = fsspec.filesystem("gs", token=token)
    if fs_result.exists(f"quakeflow_catalog/{region}/mseed_list/{year}_3c.txt"):
        return None

    # %%
    if region == "SC":
        protocol = "s3"
        bucket = "scedc-pds"
        folder = "continuous_waveforms"
        maxdepth = 2
    elif region == "NC":
        protocol = "s3"
        bucket = "ncedc-pds"
        folder = "continuous_waveforms"
        maxdepth = 3
    else:
        raise ValueError(f"Invalid region: {region}")
    fs_data = fsspec.filesystem(protocol=protocol, anon=True)

    # %%
    valid_instruments = ["BH", "HH", "EH", "HN", "DP"]
    valid_components = ["3", "2", "1", "E", "N", "Z"]

    # %%
    if not os.path.exists(f"mseed_list_3c_{region}.txt"):

        tmp_dir = f"tmp_{region}"
        if not os.path.exists(f"{tmp_dir}"):
            os.makedirs(f"{tmp_dir}")

        folder_list = []
        print(f"{bucket}/{folder}", maxdepth)

        for root, dirs, files in fs_data.walk(f"{bucket}/{folder}", maxdepth=maxdepth):
            print(f"{root}: {len(dirs)} dirs, {len(files)} files")
            folder_list.extend([f"{root}/{d}" for d in dirs])
        print(f"Number of folders: {len(folder_list)}")

        def process(rank, nodes, folder):
            print(f"{rank}/{nodes}: {folder}")

            if region == "SC":
                # mseed_list = fs.glob(f"{bucket}/{folder}/{year}/{year}_???/*_{year}???.ms")
                # mseed_list = fs_data.glob(f"{bucket}/{folder}/{year}/{year}_???/*.ms")
                mseed_list = []
                for root, dirs, files in fs_data.walk(f"{folder}", maxdepth=1):
                    mseed_list.extend([f"{protocol}://{root}/{f}" for f in files])
            elif region == "NC":
                # mseed_list = fs_data.glob(f"{bucket}/{folder}/??/{year}/???.??/*.{year}.???")
                mseed_list = []
                for root, dirs, files in fs_data.walk(f"{folder}", maxdepth=1):
                    mseed_list.extend([f"{protocol}://{root}/{f}" for f in files])

            if len(mseed_list) == 0:
                return None

            mseed_list = sorted(mseed_list)
            with open(f"{tmp_dir}/{rank}_{nodes}.txt", "w") as fp:
                fp.write("\n".join(mseed_list))

            # %% Group by station
            groups = defaultdict(list)
            for mseed in mseed_list:
                station_id, network, station, location, instrument, component, year, jday = parse_fname(mseed, region)

                if (component in valid_components) and (instrument in valid_instruments):
                    key = f"{year}_{jday}/{network}.{station}.{location}.{instrument}"
                    groups[key].append(mseed)
                # else:
                #     print(f"Invalid component: {mseed}")

            mseed_3c = []
            if len(groups) > 0:
                for key in groups.keys():
                    mseed_3c.append(",".join(sorted(groups[key])))

            with open(f"{tmp_dir}/{rank}_{nodes}_3c.txt", "w") as fp:
                fp.write("\n".join(mseed_3c))

            return mseed_3c

        num_cores = 32
        nodes = len(folder_list)
        with ThreadPoolExecutor(max_workers=num_cores) as executor:
            futures = [executor.submit(process, rank, nodes, folder) for rank, folder in enumerate(folder_list)]

        mseed_list = []
        for future in futures:
            result = future.result()
            if result is not None:
                mseed_list.extend(result)

        print(f"Total number of mseed files: {len(mseed_list)}")
        with open(f"minseed_list_3c_{region}.txt", "w") as fp:
            fp.write("\n".join(mseed_list))

    else:
        with open(f"mseed_list_3c_{region}.txt", "r") as fp:
            mseed_list = fp.read().splitlines()

    # split by year
    mseed_dir = f"mseed_list_{region}"
    if not os.path.exists(f"{mseed_dir}"):
        os.makedirs(f"{mseed_dir}")
    mseed_list = sorted(list(set(mseed_list)))
    years = sorted(list(set([x.split("/")[maxdepth + 2] for x in mseed_list])))  # 2: s3://
    print(f"Years: {years}")
    for year in years:
        mseed_by_year = [x for x in mseed_list if x.split("/")[maxdepth + 2] == year]
        with open(f"{mseed_dir}/{year}_3c.txt", "w") as fp:
            fp.write("\n".join(mseed_by_year))
        fs_result.put(f"{mseed_dir}/{year}_3c.txt", f"quakeflow_catalog/{region}/mseed_list/{year}_3c.txt")

    return 0


def split_mseed_list(
    root_path: str,
    region: str,
    year: int = 2023,
    stations: List = None,
    node_rank: int = 0,
    num_nodes: int = 1,
    protocol: str = "s3",
    bucket: str = "",
    token: Dict = None,
):

    # %%
    fs = fsspec.filesystem("gs", token=token)
    bucket = "quakeflow_catalog"
    if fs.exists(f"{bucket}/{region}/mseed_list/{year}_3c.txt"):
        with fs.open(f"{bucket}/{region}/mseed_list/{year}_3c.txt", "r") as fp:
            mseed_list = fp.read().splitlines()

    # %%
    # if stations is not None:
    #     mseed_list_filt = []
    #     for mseed in mseed_list:
    #         fname = mseed.split(",")[0].split("/")[-1]
    #         station_id, network, station, location, instrument, component, year, jday = parse_fname(fname)
    #         if station_id in stations:
    #             mseed_list_filt.append(mseed)
    #     print(f"Number of selected mseed files: {len(mseed_list_filt)} / {len(mseed_list)}")
    #     mseed_list = mseed_list_filt

    # %%
    mseed_list = sorted(list(set(mseed_list)))
    print(f"Total number of mseed files: {len(mseed_list)}")

    mseed_list = mseed_list[node_rank::num_nodes]
    print(f"Number to process by node {node_rank}/{num_nodes}: {len(mseed_list)}")

    folder = f"{region}/phasenet"
    processed = fs.glob(f"{bucket}/{folder}/{year}/????_???/*.csv")
    processed = set(processed)
    mseed_csv_set = set()
    mapping_dit = {}
    for mseed in tqdm(mseed_list, desc="Filter processed"):
        tmp = mseed.split(",")[0].lstrip("s3://").split("/")
        subdir = "/".join(tmp[2:-1])
        fname = tmp[-1].rstrip(".mseed").rstrip(".ms") + ".csv"
        tmp_name = f"{bucket}/{folder}/{subdir}/{fname}"
        mseed_csv_set.add(tmp_name)
        mapping_dit[tmp_name] = mseed
    mseed_csv_set = list(mseed_csv_set - processed)
    unprocess = sorted([mapping_dit[x] for x in mseed_csv_set], reverse=True, key=lambda x: "/".join(x.split("/")[-2:]))
    print(f"Unprocessed mseed: {len(unprocess)}")

    # %%
    # with fs.open(f"{bucket}/{folder}/mseed_list/{year}_{node_rank:03d}_{num_nodes:03d}_3c.txt", "w") as fp:
    #     fp.write("\n".join(unprocess))
    with open(f"mseed_list_{node_rank:03d}_{num_nodes:03d}.txt", "w") as fp:
        fp.write("\n".join(unprocess))
    fs.put(
        f"mseed_list_{node_rank:03d}_{num_nodes:03d}.txt",
        f"{bucket}/{region}/phasenet/mseed_list/{year}_{node_rank:03d}_{num_nodes:03d}.txt",
    )
    print(
        f"{bucket}/{region}/phasenet/mseed_list/{year}_{node_rank:03d}_{num_nodes:03d}.txt",
    )

    # return f"{bucket}/{folder}/mseed_list/{year}_{node_rank:03d}_{num_nodes:03d}_3c.txt"
    return f"mseed_list_{node_rank:03d}_{num_nodes:03d}.txt"


def run_phasenet(
    root_path: str,
    region: str,
    model_path: str = "./",
    mseed_list: str = "mseed_list.txt",
    node_rank: int = 0,
    num_nodes: int = 1,
    protocol: str = "s3",
    bucket: str = "",
    token: Dict = None,
) -> int:

    # %%
    # fs = fsspec.filesystem("gs", token=token)

    # with fs.open(mseed_list, "r") as fp:
    #     mseed_list = fp.read().splitlines()

    # with open(f"mseed_list_{node_rank:03d}_{num_nodes:03d}.txt", "w") as fp:
    #     fp.write("\n".join(mseed_list[node_rank::num_nodes]))

    # if len(mseed_list[node_rank::num_nodes]) == 0:
    #     return 0

    with open("application_default_credentials.json", "w") as fp:
        json.dump(token, fp)

    # %%
    os.system(
        f"python {model_path}/phasenet/predict.py --model={model_path}/model/190703-214543 --data_list={mseed_list}  --format=mseed --amplitude --batch_size=1 --sampling_rate=100 --highpass_filter=1.0 --result_dir={root_path}/{region}/picks_{year}/"
    )

    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Run PhaseNet on NCEDC/SCEDC data")
    parser.add_argument("--num_nodes", type=int, default=64, help="Number of nodes")
    parser.add_argument("--node_rank", type=int, default=0, help="Node rank")
    parser.add_argument("--year", type=int, default=2023, help="Year to process")
    parser.add_argument("--model_path", type=str, default="../../PhaseNet/", help="Model path")
    parser.add_argument("--root_path", type=str, default="./", help="Root path")
    parser.add_argument("--region", type=str, default="SC", help="Region to process")
    parser.add_argument("--bucket", type=str, default="quakeflow_catalog", help="Bucket")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    # %%
    args = parse_args()

    protocol = "gs"
    token_json = f"{os.environ['HOME']}/.config/gcloud/application_default_credentials.json"
    with open(token_json, "r") as fp:
        token = json.load(fp)

    region = args.region
    root_path = args.root_path
    bucket = args.bucket
    num_nodes = args.num_nodes
    node_rank = args.node_rank
    year = args.year
    print(f"{year = }")

    # %%
    token_file = f"{os.environ['HOME']}/.config/gcloud/application_default_credentials.json"
    if os.path.exists(token_file):
        with open(token_file, "r") as fp:
            token = json.load(fp)

    # %%
    # stations = pd.read_csv("stations_ncedc.csv")
    # stations["station_id"] = stations["station"] + "." + stations["network"] + "." + stations["instrument"]
    # stations = stations["station_id"].unique().tolist()
    stations = None

    collect_mseeds(
        root_path=root_path,
        region=region,
        year=year,
        node_rank=node_rank,
        num_nodes=num_nodes,
        protocol=protocol,
        bucket=bucket,
        token=token,
    )
    mseed_csv = split_mseed_list(
        root_path=args.root_path,
        region=args.region,
        year=args.year,
        stations=stations,
        node_rank=args.node_rank,
        num_nodes=args.num_nodes,
        token=token,
    )
    run_phasenet(
        root_path="./",
        region=args.region,
        model_path=args.model_path,
        mseed_list=mseed_csv,
        node_rank=args.node_rank,
        num_nodes=args.num_nodes,
        token=token,
    )
