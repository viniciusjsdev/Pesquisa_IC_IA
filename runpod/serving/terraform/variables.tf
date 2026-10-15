variable "pod_name" {
  type        = string
  description = "Name shown in RunPod."
}

variable "gpu_type_ids" {
  type        = list(string)
  description = "GPU types selected after checking current availability and price."
}

variable "data_center_ids" {
  type        = list(string)
  description = "Data centers selected for this session."
}

variable "image_name" {
  type        = string
  description = "Reviewed CUDA/vLLM image pinned to a digest or immutable tag."
}

variable "gpu_count" {
  type        = number
  description = "Explicit GPU count for this paid session."
}

variable "cloud_type" {
  type        = string
  description = "SECURE or COMMUNITY, chosen for this session."

  validation {
    condition     = contains(["SECURE", "COMMUNITY"], var.cloud_type)
    error_message = "cloud_type must be SECURE or COMMUNITY."
  }
}

variable "volume_in_gb" {
  type        = number
  description = "Persistent volume capacity selected for the artifacts."
}

variable "container_disk_in_gb" {
  type        = number
  description = "Container disk capacity selected for the image and runtime."
}
