variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "container_app_subnet_id" {
  description = "The ID of the infrastructure subnet"
  type        = string
}

variable "gateway_subnet_id" {
  description = "The ID of the gateway subnet"
  type        = string
}

variable "backend_address" {
  description = "The backend address"
  type        = string
}

variable "ui_address" {
  description = "The UI address"
  type        = string
}

variable "react_app_address" {
  description = "The react app address"
  type        = string
}

variable "gateway_public_ip_id" {
  description = "The ID of the gateway public IP"
  type        = string
}

variable "ssl_certificate_file_path" {
  description = "SSL certificate file path"
  type        = string
}

variable "ssl_certificate_file_path_2" {
  description = "SSL certificate file path"
  type        = string
}

variable "ssl_certificate_password" {
  description = "SSL certificate password"
  type        = string
}

variable "host_name" {
  description = "Host name that the application gateway will listen to"
  type        = string
}

variable "host_name_2" {
  description = "Host name that the application gateway will listen to"
  type        = string
}
