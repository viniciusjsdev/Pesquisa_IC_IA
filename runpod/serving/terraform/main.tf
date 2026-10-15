terraform {
  required_version = ">= 1.0.0"

  required_providers {
    runpod = {
      source  = "decentralized-infrastructure/runpod"
      version = "= 1.0.1"
    }
  }
}

provider "runpod" {
  # RUNPOD_API_KEY is read from the operator's environment.
}

resource "runpod_pod" "inference" {
  name                 = var.pod_name
  gpu_type_ids         = var.gpu_type_ids
  data_center_ids      = var.data_center_ids
  image_name           = var.image_name
  gpu_count            = var.gpu_count
  cloud_type           = var.cloud_type
  volume_in_gb         = var.volume_in_gb
  container_disk_in_gb = var.container_disk_in_gb
  volume_mount_path    = "/workspace"

  # Only the authenticated gateway is reachable through RunPod's HTTPS proxy.
  # vLLM itself binds to 127.0.0.1:8001 inside the Pod.
  ports = ["8000/http"]
}

output "pod_id" {
  value = runpod_pod.inference.id
}
