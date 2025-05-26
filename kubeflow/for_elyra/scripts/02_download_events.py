#!/usr/bin/env python3
"""
QuakeFlow Events Download Script
標準地震カタログをダウンロードするスクリプト
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

    print(f"Downloading events for region: {config['region']}")

    # IRIS catalog からイベントをダウンロード
    try:
        events = Client(config["client"]).get_events(
            starttime=config["starttime"],
            endtime=config["endtime"],
            minlongitude=config["xlim_degree"][0],
            maxlongitude=config["xlim_degree"][1],
            minlatitude=config["ylim_degree"][0],
            maxlatitude=config["ylim_degree"][1],
        )
    except:
        print(f"Failed to connect to {config['client']}, trying IRIS...")
        events = Client("iris").get_events(
            starttime=config["starttime"],
            endtime=config["endtime"],
            minlongitude=config["xlim_degree"][0],
            maxlongitude=config["xlim_degree"][1],
            minlatitude=config["ylim_degree"][0],
            maxlatitude=config["ylim_degree"][1],
        )

    print(f"Number of events downloaded: {len(events)}")

    # カタログを保存
    catalog = defaultdict(list)
    for event in events:
        if len(event.magnitudes) > 0:
            catalog["time"].append(event.origins[0].time.datetime)
            catalog["magnitude"].append(event.magnitudes[0].mag)
            catalog["longitude"].append(event.origins[0].longitude)
            catalog["latitude"].append(event.origins[0].latitude)
            catalog["depth(m)"].append(event.origins[0].depth)

    catalog = pd.DataFrame.from_dict(catalog).sort_values(["time"])
    catalog.to_csv(
        "standard_catalog.csv",
        index=False,
        float_format="%.3f",
        date_format="%Y-%m-%dT%H:%M:%S.%f",
        columns=["time", "magnitude", "longitude", "latitude", "depth(m)"],
    )

    print(f"Standard catalog saved with {len(catalog)} events")

    # MinIOにアップロード
    try:
        from minio import Minio
        minioClient = Minio(s3_url, access_key="minio", secret_key="minio123", secure=secure)
        if not minioClient.bucket_exists(bucket_name):
            minioClient.make_bucket(bucket_name)

        minioClient.fput_object(
            bucket_name,
            f"{config['region']}/standard_catalog.csv",
            "standard_catalog.csv",
        )
        print(f"Standard catalog uploaded to MinIO: {bucket_name}")
    except Exception as err:
        print(f"WARNING: Could not upload to MinIO: {err}")

    # プロット作成
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(catalog["longitude"], catalog["latitude"], ".", markersize=1)
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.axis("scaled")
        plt.xlim(config["xlim_degree"])
        plt.ylim(config["ylim_degree"])
        plt.title(f"Events Location - {config['region']}")
        plt.savefig("events_location.png", dpi=150, bbox_inches='tight')
        plt.close()

        plt.figure(figsize=(12, 6))
        plt.plot_date(catalog["time"], catalog["magnitude"], ".", markersize=1)
        plt.gcf().autofmt_xdate()
        plt.ylabel("Magnitude")
        plt.title(f"Events Magnitude vs Time - {config['region']} (Total: {len(events)})")
        plt.savefig("events_magnitude_time.png", dpi=150, bbox_inches='tight')
        plt.close()
        
        print("Event plots saved")
    except Exception as err:
        print(f"WARNING: Could not create plots: {err}")

if __name__ == "__main__":
    main() 