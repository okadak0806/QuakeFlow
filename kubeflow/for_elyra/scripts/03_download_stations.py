#!/usr/bin/env python3
"""
QuakeFlow Stations Download Script
地震観測点情報をダウンロードするスクリプト
"""

import json
import os
import pickle
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt
import obspy
import pandas as pd
from obspy.clients.fdsn import Client

matplotlib.use("agg")

def main():
    # 環境変数から設定を取得
    bucket_name = os.environ.get('BUCKET_NAME', 'catalogs')
    s3_url = os.environ.get('S3_URL', 'minio-service:9000')
    secure = os.environ.get('SECURE', 'false').lower() == 'true'

    # 設定ファイルを読み込み
    with open("config.json", "r") as fp:
        config = json.load(fp)

    print(f"Downloading stations for region: {config['region']}")
    print("Networks:", ",".join(config["networks"]))

    # 観測点をダウンロード
    try:
        stations = Client(config["client"]).get_stations(
            network=",".join(config["networks"]),
            station="*",
            starttime=config["starttime"],
            endtime=config["endtime"],
            minlongitude=config["xlim_degree"][0],
            maxlongitude=config["xlim_degree"][1],
            minlatitude=config["ylim_degree"][0],
            maxlatitude=config["ylim_degree"][1],
            channel=config["channels"],
            level="response",
        )
    except Exception as err:
        print(f"Error downloading stations: {err}")
        # 空のInventoryを作成
        stations = obspy.Inventory()

    print(f"Number of stations downloaded: {sum([len(x) for x in stations])}")

    # 観測点情報を保存
    station_locs = defaultdict(dict)
    for network in stations:
        for station in network:
            for chn in station:
                sid = f"{network.code}.{station.code}.{chn.location_code}.{chn.code[:-1]}"
                if sid in station_locs:
                    if chn.code[-1] not in station_locs[sid]["component"]:
                        station_locs[sid]["component"].append(chn.code[-1])
                        station_locs[sid]["response"].append(round(chn.response.instrument_sensitivity.value, 2))
                else:
                    tmp_dict = {
                        "longitude": chn.longitude,
                        "latitude": chn.latitude,
                        "elevation(m)": chn.elevation,
                        "component": [chn.code[-1]],
                        "response": [round(chn.response.instrument_sensitivity.value, 2)],
                        "unit": chn.response.instrument_sensitivity.input_units.lower(),
                    }
                    station_locs[sid] = tmp_dict

    # JSONファイルとして保存
    with open("stations.json", "w") as fp:
        json.dump(station_locs, fp, indent=2)

    # Pickleファイルとして保存
    with open("stations.pkl", "wb") as fp:
        pickle.dump(stations, fp)

    print(f"Station information saved for {len(station_locs)} stations")

    # MinIOにアップロード
    try:
        from minio import Minio
        minioClient = Minio(s3_url, access_key="minio", secret_key="minio123", secure=secure)
        if not minioClient.bucket_exists(bucket_name):
            minioClient.make_bucket(bucket_name)

        minioClient.fput_object(
            bucket_name,
            f"{config['region']}/stations.json",
            "stations.json",
        )
        minioClient.fput_object(
            bucket_name,
            f"{config['region']}/stations.pkl",
            "stations.pkl",
        )
        print(f"Station files uploaded to MinIO: {bucket_name}")
    except Exception as err:
        print(f"WARNING: Could not upload to MinIO: {err}")

    # プロット作成
    try:
        if len(station_locs) > 0:
            station_df = pd.DataFrame.from_dict(station_locs, orient="index")
            
            plt.figure(figsize=(10, 8))
            plt.plot(station_df["longitude"], station_df["latitude"], "^", 
                    markersize=6, color='red', label="Stations")
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            plt.axis("scaled")
            plt.xlim(config["xlim_degree"])
            plt.ylim(config["ylim_degree"])
            plt.legend()
            plt.title(f"Station Locations - {config['region']} (Total: {len(station_df)})")
            plt.grid(True, alpha=0.3)
            plt.savefig("stations_location.png", dpi=150, bbox_inches='tight')
            plt.close()
            
            print("Station plot saved")
        else:
            print("No stations to plot")
    except Exception as err:
        print(f"WARNING: Could not create station plot: {err}")

if __name__ == "__main__":
    main() 