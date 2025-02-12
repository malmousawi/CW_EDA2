
output "worker_vm_ips" {
  value = harvester_virtualmachine.worker[*].network_interface[0].ip_address
}

output "worker_vm_ids" {
  value = harvester_virtualmachine.worker[*].id
}



