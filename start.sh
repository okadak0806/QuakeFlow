#!/bin/bash
#
pkill -f "kubectl.*port-forward"

kubectl port-forward $(kubectl get pods -n kubeflow | grep ml-pipeline-ui | cut -d' ' -f1) 31380:3000 -n kubeflow &

grep -q "127.0.0.1 minio-service.kubeflow.svc.cluster.local" /etc/hosts || echo "127.0.0.1 minio-service.kubeflow.svc.cluster.local" | sudo tee -a /etc/hosts

kubectl port-forward $(kubectl get pods -n kubeflow | grep minio | cut -d' ' -f1) 9000:9000 -n kubeflow &
