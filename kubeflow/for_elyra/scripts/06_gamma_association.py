#!/usr/bin/env python3
"""
QuakeFlow GaMMA Association Script
PhaseNetで検出されたP/S波を関連付けて地震イベントを特定するスクリプト
"""

import json
import os
import pickle
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from gamma.utils import association
from pyproj import Proj
from tqdm import tqdm

def main():
    # 環境変数から設定を取得
    node_i = int(os.environ.get('NODE_I', '0'))
    bucket_name = os.environ.get('BUCKET_NAME', 'catalogs')
    s3_url = os.environ.get('S3_URL', 'minio-service:9000')
    secure = os.environ.get('SECURE', 'false').lower() == 'true'

    # 設定ファイルを読み込み
    with open("config.json", "r") as fp:
        config = json.load(fp)

    print(f"Running GaMMA association for region: {config['region']}")

    # PhaseNetの結果を読み込み
    try:
        picks = pd.read_csv("picks.csv", parse_dates=["phase_time"])
    except FileNotFoundError:
        print("ERROR: picks.csv not found. Make sure PhaseNet step completed successfully.")
        return

    # 観測点情報を読み込み
    with open("stations.json", "r") as fp:
        stations = json.load(fp)

    # データフレームに変換
    picks["id"] = picks["station_id"]
    picks["timestamp"] = picks["phase_time"]
    picks["amp"] = picks["phase_amp"]
    picks["type"] = picks["phase_type"]
    picks["prob"] = picks["phase_score"]

    stations = pd.DataFrame.from_dict(stations, orient="index")
    stations["id"] = stations.index

    # 座標変換
    proj = Proj(f"+proj=sterea +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
    stations[["x(km)", "y(km)"]] = stations.apply(
        lambda x: pd.Series(proj(longitude=x.longitude, latitude=x.latitude)), axis=1
    )
    stations["z(km)"] = stations["elevation(m)"].apply(lambda x: -x / 1e3)

    print(f"Loaded {len(picks)} picks from {len(stations)} stations")

    # GaMMA設定
    config["use_dbscan"] = True
    config["use_amplitude"] = True
    config["method"] = "BGMM"
    
    if config["method"] == "BGMM":
        config["oversample_factor"] = 4
    if config["method"] == "GMM":
        config["oversample_factor"] = 1

    # 地震位置決定設定
    config["dims"] = ["x(km)", "y(km)", "z(km)"]
    config["vel"] = {"p": 6.0, "s": 6.0 / 1.73}
    config["x(km)"] = (np.array(config["xlim_degree"]) - np.array(config["center"][0])) * config["degree2km"]
    config["y(km)"] = (np.array(config["ylim_degree"]) - np.array(config["center"][1])) * config["degree2km"]
    config["z(km)"] = (0, 60)
    config["bfgs_bounds"] = (
        (config["x(km)"][0] - 1, config["x(km)"][1] + 1),
        (config["y(km)"][0] - 1, config["y(km)"][1] + 1),
        (0, config["z(km)"][1] + 1),
        (None, None),
    )

    # DBSCAN設定
    config["dbscan_eps"] = 10
    config["dbscan_min_samples"] = 3

    # フィルタリング設定
    config["min_picks_per_eq"] = min(10, len(stations) // 2)
    config["min_p_picks_per_eq"] = 0
    config["min_s_picks_per_eq"] = 0
    config["max_sigma11"] = 2.0
    config["max_sigma22"] = 2.0
    config["max_sigma12"] = 1.0

    # 振幅を使用する場合のフィルタリング
    if config["use_amplitude"]:
        picks = picks[picks["amp"] != -1]

    print("GaMMA configuration:")
    for k, v in config.items():
        if k not in ["xlim_degree", "ylim_degree"]:  # 長いリストは省略
            print(f"  {k}: {v}")

    # GaMMA関連付け実行
    print("Running GaMMA association...")
    event_idx0 = 1
    catalogs, assignments = association(picks, stations, config, event_idx0, method=config["method"])
    event_idx0 += len(catalogs)

    print(f"GaMMA found {len(catalogs)} events from {len(picks)} picks")

    # カタログ作成
    catalogs = pd.DataFrame(
        catalogs,
        columns=["time"] + config["dims"] + [
            "magnitude", "sigma_time", "sigma_amp", "cov_time_amp", 
            "event_index", "gamma_score"
        ],
    )

    # 座標を経度緯度に変換
    catalogs[["longitude", "latitude"]] = catalogs.apply(
        lambda x: pd.Series(proj(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)),
        axis=1,
    )
    catalogs["depth(m)"] = catalogs["z(km)"].apply(lambda x: x * 1e3)

    # カタログを保存
    catalogs.sort_values(by=["time"], inplace=True)
    catalogs.to_csv(
        "gamma_catalog.csv",
        index=False,
        float_format="%.3f",
        date_format="%Y-%m-%dT%H:%M:%S.%f",
        columns=[
            "time", "magnitude", "longitude", "latitude", "depth(m)",
            "sigma_time", "sigma_amp", "cov_time_amp", "gamma_score", "event_index",
        ],
    )

    # 関連付け結果をピックに追加
    assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])
    picks = picks.join(assignments.set_index("pick_index")).fillna(-1).astype({"event_index": int})
    picks.sort_values(by=["timestamp"], inplace=True)
    picks.to_csv(
        "gamma_picks.csv",
        index=False,
        date_format="%Y-%m-%dT%H:%M:%S.%f",
        columns=[
            "station_id", "phase_time", "phase_type", "phase_score", 
            "phase_amp", "gamma_score", "event_index",
        ],
    )

    print(f"Saved {len(catalogs)} events and {len(picks)} picks")

    # MinIOにアップロード
    try:
        from minio import Minio
        minioClient = Minio(s3_url, access_key="minio", secret_key="minio123", secure=secure)
        if not minioClient.bucket_exists(bucket_name):
            minioClient.make_bucket(bucket_name)

        minioClient.fput_object(
            bucket_name,
            f"{config['region']}/gamma/catalog_{node_i:03d}.csv",
            "gamma_catalog.csv",
        )
        minioClient.fput_object(
            bucket_name,
            f"{config['region']}/gamma/picks_{node_i:03d}.csv",
            "gamma_picks.csv",
        )
        print(f"Results uploaded to MinIO: {bucket_name}")
    except Exception as err:
        print(f"WARNING: Could not upload to MinIO: {err}")

    print("GaMMA association completed successfully")

if __name__ == "__main__":
    main() 