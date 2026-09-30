#!/usr/bin/env fish
# PS-023 Fedora KVM/Libvirt Setup Script (Fish Shell)

echo "=== PS-023: Fedora KVM & Libvirt Setup Guide ==="

# 1. Check CPU virtualization support
echo "Checking CPU virtualization flags (vmx for Intel, svm for AMD)..."
if grep -E -q '(vmx|svm)' /proc/cpuinfo
    echo "[OK] Hardware virtualization (AMD-V / Intel VT-x) is supported by your CPU!"
else
    echo "[ERROR] Hardware virtualization is not enabled in BIOS/UEFI. Please enable AMD-V/SVM in BIOS."
    exit 1
end

# 2. Check /dev/kvm
if test -e /dev/kvm
    echo "[OK] /dev/kvm device node is present."
else
    echo "[INFO] /dev/kvm not found. Installing kvm kernel module..."
    sudo modprobe kvm
    sudo modprobe kvm_amd 2>/dev/null
    sudo modprobe kvm_intel 2>/dev/null
end

echo ""
echo "=== Required Fedora DNF Packages ==="
echo "To enable real KVM/libvirt execution on Fedora, install the following packages:"
echo "    sudo dnf install -y qemu-kvm libvirt virt-install virt-manager python3-libvirt"
echo ""
echo "=== Service & Group Configuration ==="
echo "1. Enable and start libvirtd / virtqemud daemon:"
echo "    sudo systemctl enable --now virtqemud.socket"
echo "    sudo systemctl enable --now libvirtd"
echo ""
echo "2. Add your user to the libvirt group (avoids needing sudo for virsh):"
echo "    sudo usermod -aG libvirt "(whoami)
echo "    newgrp libvirt"
echo ""
echo "3. Verify connection:"
echo "    virsh -c qemu:///system list --all"
echo ""
echo "After configuring, edit .env to set:"
echo "    DEMO_MODE=false"
echo "    LIBVIRT_URI=qemu:///system"
