data "harvester_image" "img" {
  display_name = var.img_display_name
  namespace    = "harvester-public"
}

data "harvester_ssh_key" "mysshkey" {
  name      = var.keyname
  namespace = var.namespace
}

resource "random_id" "secret" {
  byte_length = 5
}


# Generate the first SSH key
resource "tls_private_key" "ssh_key_1" {
  algorithm = "ED25519"
}

resource "local_file" "ssh_key_1" {
  filename = "ssh_key_1.pem"
  content  = tls_private_key.ssh_key_1.private_key_openssh
}

resource "harvester_cloudinit_secret" "cloud-config" {
  name      = "cloud-config-${random_id.secret.hex}"
  namespace = var.namespace

  user_data = templatefile("cloud-init.tmpl.yml", {
      public_key_openssh  = tls_private_key.ssh_key_1.public_key_openssh,
    })
}

# Host VM
resource "harvester_virtualmachine" "host" {
  count                = 1
  name                 = "${var.username}-host-${random_id.secret.hex}"
  namespace            = var.namespace
  restart_after_update = true

  description = "Host VM"

  cpu    = 2
  memory = "4Gi"

  efi         = true
  secure_boot = false

  run_strategy    = "RerunOnFailure"
  hostname        = "${var.username}-host"
  reserved_memory = "100Mi"
  machine_type    = "q35"

  network_interface {
    name           = "nic-1"
    wait_for_lease = true
    type           = "bridge"
    network_name   = var.network_name
  }

  disk {
    name       = "rootdisk"
    type       = "disk"
    size       = "10Gi"
    bus        = "virtio"
    boot_order = 1

    image       = data.harvester_image.img.id
    auto_delete = true
  }

  cloudinit {
    user_data_secret_name = harvester_cloudinit_secret.cloud-config.name
  }

  tags = {
    condenser_ingress_prometheus_hostname = "${var.username}-ucl-prometheus"
    condenser_ingress_prometheus_port     = 9090
    condenser_ingress_grafana_hostname    = "${var.username}-ucl-grafana"
    condenser_ingress_os_hostname      = "${var.username}-ucl-s3"
    condenser_ingress_os_port          = 9000
    condenser_ingress_os_protocol = "https"
    condenser_ingress_os_nginx_proxy-body-size = "100000m"
    condenser_ingress_grafana_port        = 3000
    condenser_ingress_isAllowed           = true
    condenser_ingress_isEnabled           = true
    condenser_ingress_cons_port = 9001
    condenser_ingress_cons_protocol = "https"
    condenser_ingress_cons_hostname = "${var.username}-ucl-cons"
    condenser_ingress_cons_nginx_proxy-body-size = "100000m"
  }
}

# Worker VMs
resource "harvester_virtualmachine" "worker" {
  count                = 4
  name                 = "${var.username}-worker-${format("%02d", count.index + 1)}-${random_id.secret.hex}"
  namespace            = var.namespace
  restart_after_update = true

  description = "Worker VM"

  cpu    = 4
  memory = "32Gi"

  efi         = true
  secure_boot = false

  run_strategy    = "RerunOnFailure"
  hostname        = "${var.username}-worker-${format("%02d", count.index + 1)}"
  reserved_memory = "100Mi"
  machine_type    = "q35"

  network_interface {
    name           = "nic-1"
    wait_for_lease = true
    type           = "bridge"
    network_name   = var.network_name
  }

  disk {
    name       = "rootdisk"
    type       = "disk"
    size       = "50Gi"
    bus        = "virtio"
    boot_order = 1

    image       = data.harvester_image.img.id
    auto_delete = true
  }

  disk {
    name       = "datadisk"
    type       = "disk"
    size       = "200Gi"
    bus        = "virtio"
    boot_order = 2

    auto_delete = true
  }

  cloudinit {
    user_data_secret_name = harvester_cloudinit_secret.cloud-config.name
  }

  tags = {
    condenser_ingress_node_hostname = "${var.username}-ucl-node"
    condenser_ingress_node_port     = 9100
    condenser_ingress_isAllowed     = true
    condenser_ingress_isEnabled     = true
  }
}


