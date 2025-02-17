#!/usr/bin/env python3

import json
import subprocess

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
        # Extract worker VM IPs from "value" field
        worker_vm_ips = terraform_output.get("worker_vm_ips", {}).get("value", [])
        # Extract host VM IP from "host_vm_ip" (if available)
        host_vm_ip = terraform_output.get("host_vm_ip", {}).get("value", None)
    except Exception as e:
        print(f"Error generating inventory: {e}")
        return {}

    ansible_user = "almalinux"
    # Using SSH agent forwarding, so we don't specify a private key file.
    common_vars = {
        "ansible_user": ansible_user,
        "ansible_ssh_common_args": "-o ForwardAgent=yes"
    }

    # Build _meta hostvars for workers
    worker_hostvars = {
        ip: {
            "ansible_host": ip,
            **common_vars
        }
        for ip in worker_vm_ips
    }

    # Build inventory groups
    inventory = {
        "_meta": {
            "hostvars": worker_hostvars
        },
        "worker": {
            "hosts": {ip: {} for ip in worker_vm_ips}
        }
    }

    # If host_vm_ip exists, add it to _meta and also create a 'host' group.
    if host_vm_ip:
        inventory["_meta"]["hostvars"][host_vm_ip] = {
            "ansible_host": host_vm_ip,
            **common_vars
        }
        inventory["host"] = {
            "hosts": {
                host_vm_ip: {}
            }
        }

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
            print(f"Error generating inventory: {e}")
            print("{}")
    elif args.host:
        print(json.dumps({}))
    else:
        parser.print_help()

