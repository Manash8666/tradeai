#!/usr/bin/env bash
set -euo pipefail

# Bare-Metal Host System Provisioning for Low-Latency Execution
# 1. Allocate 2048 x 2MB Hugepages (Total 4GB)
echo 2048 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
sudo mkdir -p /dev/hugepages
sudo mount -t hugetlbfs nodev /dev/hugepages || true

# 2. Maximize Shared Memory and Network Ring Limits
sudo sysctl -w vm.max_map_count=1048576
sudo sysctl -w fs.file-max=2097152
sudo sysctl -w net.core.bpf_jit_enable=1
sudo sysctl -w net.core.bpf_jit_harden=0

# 3. Increase NIC Ring Buffers (e.g. eth0)
NIC_IFACE="${1:-eth0}"
sudo ethtool -G "${NIC_IFACE}" rx 4096 tx 4096 || true
sudo ethtool -L "${NIC_IFACE}" combined 4 || true

# 4. Set CPU Governor to maximum performance (disable clock throttling)
for CPU in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo "performance" | sudo tee "$CPU" || true
done

echo "Host infrastructure configured for zero-copy low-latency execution."
