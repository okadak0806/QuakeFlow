# Ansible GPU-enabled Kubernetes Installation (Ubuntu 24.04)

Terraformで作成したVRTサーバーに[さくらクラウド公式マニュアル](https://manual.sakura.ad.jp/cloud/server/gpu-plan.html#cuda-toolkit-gpu)に従ってCUDA、Kubernetes、GPU Container Toolkitを自動インストールするAnsible構成です。

## 前提条件

1. **SSHキーの設定**
   ```bash
   # SSHキーを生成（まだ作成していない場合）
   ssh-keygen -t rsa -b 4096
   
   # 公開鍵をサーバーに登録（Terraformのuser_dataで自動設定）
   ```

2. **Ansibleのインストール**
   ```bash
   sudo apt update
   sudo apt install ansible
   ```

## インストール内容（Ubuntu 24.04準拠）

1. **CUDA Toolkit 12.9**
   - NVIDIA公式リポジトリからインストール
   - Ubuntu 24.04専用パッケージ

2. **NVIDIA Driver 535**
   - Tesla V100 GPU対応
   - nvidia-smiコマンドでGPU認識確認

3. **NVIDIA Container Toolkit**
   - DockerでGPUを利用可能に
   - nvidia-ctk runtimeでDocker設定

4. **Docker**
   - GPU対応Docker環境
   - NVIDIA Container Runtime設定

5. **Kubernetes v1.32**
   - kubelet, kubeadm, kubectl
   - Flannel CNI
   - 単一ノードクラスター設定

6. **NVIDIA Device Plugin**
   - KubernetesでGPUリソース管理
   - Pod内でGPU利用可能

## 使用方法

### 1. 手動実行

```bash
# Terraformでサーバー作成
cd terraform
terraform apply -auto-approve

# サーバーIPを取得
SERVER_IP=$(terraform output -raw server_ip)
export TF_VAR_server_ip="$SERVER_IP"

# AnsibleでCUDAインストール
cd ../ansible
ansible-playbook -i inventory.yml playbook.yml -v
```

### 2. 自動実行スクリプト

```bash
# 全自動実行（Terraform + Ansible）
./ansible/run_cuda_install.sh
```

## 構成ファイル

- `inventory.yml`: Ansibleインベントリ設定
- `playbook.yml`: メインプレイブック
- `roles/cuda/tasks/main.yml`: CUDAインストールロール（Ubuntu 24.04準拠）

## 検証

インストール完了後、以下でGPUとKubernetesを確認できます：

```bash
# GPU情報表示
ssh ubuntu@<SERVER_IP> 'nvidia-smi'

# Docker GPU対応確認
ssh ubuntu@<SERVER_IP> 'docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu20.04 nvidia-smi'

# Kubernetesクラスター確認
ssh ubuntu@<SERVER_IP> 'kubectl get nodes -o wide'

# GPU利用可能確認
ssh ubuntu@<SERVER_IP> 'kubectl get nodes -o json | jq ".items[].status.capacity.\"nvidia.com/gpu\""'

# GPUデバイス確認
ssh ubuntu@<SERVER_IP> 'lspci | grep -i nvidia'
```

## 期待される出力

### nvidia-smi
```
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 575.57.08              Driver Version: 575.57.08      CUDA Version: 12.9     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA V100-SXM2-16GB          Off |   00000000:07:00.0 Off |                    0 |
| N/A   31C    P0             45W /  300W |       0MiB / 16160MiB |      1%      Default |
+-----------------------------------------+------------------------+----------------------+
```

## トラブルシューティング

### SSH接続エラー
- SSHキーが正しく設定されているか確認
- サーバーの起動完了を待機

### CUDAインストールエラー
- インターネット接続を確認
- パッケージキャッシュをクリア
- 再実行前にサーバーを再起動

### GPU認識エラー
- サーバー再起動後に再度実行
- `lspci | grep -i nvidia`でデバイス確認
