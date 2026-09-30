# Networking Architecture in PS-023

## 1. Network Topology

```text
Host Physical Interface (e.g. wlan0 / eth0)
      |
   iptables / nftables NAT Masquerade
      |
libvirt Virtual Bridge: virbr0 (192.168.122.1/24)
      |
   dnsmasq (DHCP & DNS for VMs)
      |
   +-- vnet0 --------> [ VM 1 Interface: 192.168.122.105 ]
   +-- vnet1 --------> [ VM 2 Interface: 192.168.122.106 ]
```

## 2. NAT vs Linux Bridge

| Approach | How it works | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **NAT (virbr0 default)** *(Selected)* | libvirt creates a virtual switch with private subnet (192.168.122.0/24) and routes outbound traffic via host NAT. | Zero disruption to host WiFi or ethernet. Works out of the box on laptops. Safe. | External LAN cannot directly ping VMs without port forwarding. |
| **Direct Host Bridge (br0)** | Physical host interface is enslaved into a network bridge. | VMs appear directly on the physical LAN. | Dangerous to automate: breaks WiFi connections and can drop host SSH sessions if misconfigured. |

## 3. Network Safety Principle
PS-023 **never** modifies the host's physical network configuration. It utilizes the non-destructive standard libvirt `default` NAT network.
