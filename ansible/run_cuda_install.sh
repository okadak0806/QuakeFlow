#!/bin/bash
# Terraform + Ansible 連携スクリプト
# CUDAインストール自動化

set -e

echo "=== Terraform + Ansible CUDA Installation ==="

# 1. Terraformでサーバー作成
echo "Step 1: Creating VRT server with Terraform..."
cd terraform
terraform apply -auto-approve

# サーバーIPを取得
SERVER_IP=$(terraform output -raw server_ip)
echo "Server IP: $SERVER_IP"

# 環境変数として設定
export TF_VAR_server_ip="$SERVER_IP"

# 2. サーバー起動を待機
echo "Step 2: Waiting for server to be ready..."
sleep 60

# 3. AnsibleでCUDA + Kubernetes + GPU環境構築
echo "Step 3: Installing CUDA, Kubernetes and GPU Support with Ansible..."
cd ../ansible

# SSHキー確認
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "ERROR: SSH private key not found at ~/.ssh/id_rsa"
    echo "Please generate SSH key: ssh-keygen -t rsa -b 4096"
    exit 1
fi

# sudo権限確認と設定
echo "Checking and configuring sudo permissions on remote server..."
# 古いホストキーを削除
ssh-keygen -f ~/.ssh/known_hosts -R "$SERVER_IP" 2>/dev/null || true

# sudo設定を確認・実行
if ! ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa ubuntu@$SERVER_IP 'sudo -n true' 2>/dev/null; then
    echo "Configuring password-less sudo..."
    # ubuntuユーザーでSSHして、一時的にパスワード認証でsudo実行
    ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa ubuntu@$SERVER_IP 'echo "ubuntu" | sudo -S sh -c "echo \"ubuntu ALL=(ALL) NOPASSWD:ALL\" > /etc/sudoers.d/90-ubuntu-user && chmod 440 /etc/sudoers.d/90-ubuntu-user"' || {
        echo "Manual sudo setup required. Please SSH and run:"
        echo "ssh ubuntu@$SERVER_IP"
        echo "sudo echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-ubuntu-user"
        exit 1
    }
fi

# Ansible実行
ansible-playbook -i inventory.yml playbook.yml -v

echo "=== GPU-enabled Kubernetes Installation Complete ==="
echo "Server IP: $SERVER_IP"
echo "SSH: ssh ubuntu@$SERVER_IP"
echo "GPU Check: ssh ubuntu@$SERVER_IP 'nvidia-smi'"
echo "Docker GPU Test: ssh ubuntu@$SERVER_IP 'docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu20.04 nvidia-smi'"
echo "Kubernetes Check: ssh ubuntu@$SERVER_IP 'kubectl get nodes -o wide'"
echo "GPU Nodes: ssh ubuntu@$SERVER_IP 'kubectl get nodes -o json | jq \".items[].status.capacity.\\\"nvidia.com/gpu\\\"\"'"
