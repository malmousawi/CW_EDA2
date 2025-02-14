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
    """Generate Ansible inventory from Terraform outputs."""
    try:
        # Fetch full Terraform output as JSON
        terraform_output = json.loads(run(["terraform", "output", "--json"]))

        # Extract worker VM IPs from "value" field
        worker_vm_ips = terraform_output.get("worker_vm_ips", {}).get("value", [])

    except Exception as e:
        print(f"Error generating inventory: {e}")
        return {}

    # Define common SSH variables
    ansible_user = "almalinux"
    private_key_file = "/home/almalinux/CW_EDA2/ssh_key_1.pem"  # Adjust path as needed

    # Use IPs directly as host keys instead of worker1, worker2, etc.
    inventory = {
        "_meta": {
            "hostvars": {
                ip: {
                    "ansible_host": ip,
                    "ansible_user": ansible_user,
                    "ansible_ssh_private_key_file": private_key_file,
                }
                for ip in worker_vm_ips
            }
        },
        "worker": {
            "hosts": {ip: {} for ip in worker_vm_ips}
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

