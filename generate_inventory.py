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
        # Fetch IPs from Terraform outputs
        worker_vm_ips = json.loads(run(["terraform", "output", "--json", "worker_vm_ips"]))

        # Extract the "value" key if outputs are not directly lists
        worker_vm_ips = worker_vm_ips if isinstance(worker_vm_ips, list) else worker_vm_ips.get("value", [])

    except Exception as e:
        print(f"Error generating inventory: {e}")
        return {}

    # Define common SSH variables
    ansible_user = "almalinux"
    private_key_file = "/home/almalinux/eda2_cw/ssh_key_1.pem"  # Replace with the actual path to your private key

    # Build inventory
    inventory = {
        "_meta": {
            "hostvars": {
                ip: {
                    "ansible_ssh_host": ip,
                    "ansible_user": ansible_user,
                    "ansible_ssh_private_key_file": private_key_file,
                }
                for ip in worker_vm_ips
            }
        },
        "worker": {"hosts": worker_vm_ips},
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
        # Single host vars can be returned as an empty object (not used in this setup)
        print(json.dumps({}))
    else:
        parser.print_help()

