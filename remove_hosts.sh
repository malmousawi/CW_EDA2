#!/bin/bash
# remove_known_hosts.sh
#
# This script removes old SSH host keys for all new VMs generated by Terraform.
# It reads the Terraform output (assumed to be JSON) and uses jq to extract the IPs.
# It then calls ssh-keygen -R on each IP.
#
# Usage: ./remove_known_hosts.sh

# Ensure jq and terraform are installed
if ! command -v jq &>/dev/null; then
    echo "jq is not installed. Please install jq and try again."
    exit 1
fi

if ! command -v terraform &>/dev/null; then
    echo "terraform is not installed or not in PATH. Please install terraform and try again."
    exit 1
fi

# Remove worker VMs from known_hosts
worker_ips=$(terraform output -json worker_vm_ips | jq -r '.[]')
if [ -n "$worker_ips" ]; then
    echo "Removing SSH keys for worker VMs:"
    for ip in $worker_ips; do
        echo "  Removing $ip..."
        ssh-keygen -R "$ip"
    done
else
    echo "No worker_vm_ips found in Terraform output."
fi

# Remove host VM(s) from known_hosts (assuming host_vm_ips is a list and you want to remove all entries)
host_ips=$(terraform output -json host_vm_ips | jq -r '.[]')
if [ -n "$host_ips" ]; then
    echo "Removing SSH keys for host VMs:"
    for ip in $host_ips; do
        echo "  Removing $ip..."
        ssh-keygen -R "$ip"
    done
else
    echo "No host_vm_ips found in Terraform output."
fi

echo "Old SSH host keys removed."

