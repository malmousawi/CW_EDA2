#!/usr/bin/env python3

import json
import subprocess
import sys

def run(command):
    """Run a shell command and return its output."""
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {command}\n{result.stderr}")
    return result.stdout.strip()

def generate_inventory():
    """Generate Ansible inventory from Terraform outputs using SSH agent forwarding."""
    try:
        # Fetch full Terraform output as JSON
        terraform_output = json.loads(run(["terraform", "output", "--json"]))
        # Extract worker VM IPs from "value" field (expected as a list)
        worker_vm_ips = terraform_output.get("worker_vm_ips", {}).get("value", [])
        # Extract host VM IP(s) from "host_vm_ips" (if available)
        host_vm_ip = terraform_output.get("host_vm_ips", {}).get("value", [])
    except Exception as e:
        print(f"Error generating inventory: {e}", file=sys.stderr)
        return {}

    # Debug output: show what IPs were found
    print("DEBUG: Worker VM IPs found:", worker_vm_ips, file=sys.stderr)
    print("DEBUG: Host VM IP found:", host_vm_ip, file=sys.stderr)

    # If both are empty, warn the user
    if not worker_vm_ips and not host_vm_ip:
        print("WARNING: No VM IPs found in Terraform output.", file=sys.stderr)
        return {}

    ansible_user = "almalinux"
    # Using SSH agent forwarding, so we don't specify a private key file.
    common_vars = {
        "ansible_user": ansible_user,
        "ansible_ssh_common_args": "-o ForwardAgent=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    }

    # Build _meta hostvars for worker VMs
    worker_hostvars = {
        ip: {
            "ansible_host": ip,
            **common_vars
        }
        for ip in worker_vm_ips
    }

    # Start building the inventory with both 'worker' and 'host' groups.
    inventory = {
        "_meta": {
            "hostvars": worker_hostvars.copy()  # start with worker hostvars
        },
        "worker": {
            "hosts": {ip: {} for ip in worker_vm_ips}
        },
        "host": {
            "hosts": {}  # will add the host VM here if available
        }
    }

    # If a host VM IP is available, extract the first IP from the list
    if host_vm_ip:
        if isinstance(host_vm_ip, list):
            host_vm_ip = host_vm_ip[0] if host_vm_ip else None
        if host_vm_ip:
            inventory["_meta"]["hostvars"][host_vm_ip] = {
                "ansible_host": host_vm_ip,
                **common_vars
            }
            inventory["host"]["hosts"][host_vm_ip] = {}

    return inventory

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Ansible inventory from Terraform outputs.")
    parser.add_argument("--list", action="store_true", help="Generate full inventory")
    parser.add_argument("--host", help="Generate inventory for a single host")

    args = parser.parse_args()

    if args.list:
        try:
            inventory = generate_inventory()
            print(json.dumps(inventory, indent=4))
        except Exception as e:
            print(f"Error generating inventory: {e}", file=sys.stderr)
            print("{}")
    elif args.host:
        print(json.dumps({}))
    else:
        parser.print_help()

