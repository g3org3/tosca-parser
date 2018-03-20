# tosca-parser

## Usage

### Clone or fork the repo
```sh
git clone https://github.com/g3org3/tosca-parser
cd tosca-parser

# If you fork, you might want to add this for fetching updates.
git remote add upstream https://github.com/g3org3/tosca-parser

# fetch an update
git fetch upstream
git rebase upstream/master
```

### Lazy-way
```sh
# Only the First Time 
make install

# Every time to build and replace
make
```

### Don't like lazy-way then...

Install dependencies
```sh
cd tosca-parser # to this repo
pip install -r requirements.txt
```
Build & install the tool
```sh
python setup.py install
```


Helpful Links
- [How to install pip](https://pip.pypa.io/en/stable/installing/)
- [How to mange python versions?](https://github.com/pyenv/pyenv#homebrew-on-mac-os-x)

Ready to use! 🔥
```sh
tosca-parser -h
#
tosca-parser -c ./path-to/file-conf.yml
```

Example YAML conf
```yml
# tosca_definitions_version: tosca_simple_yaml_1_0
tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0
description: example for a NSD with existing network.

imports:

topology_template:


  inputs:
    network_name:
      type: string
      default: admin_internal_net
    odl:
      type: string
      default: 192.168.111.28:8181


  node_templates:

    VM1:
      type: tosca.nodes.Compute
      capabilities:
        # Host container properties
        host:
         properties:
           num_cpus: 2
           disk_size: 10 GB
           mem_size: 512 MB
        # Guest Operating System properties
        os:
          properties:
            # host Operating System image properties
            architecture: x86_64
            type: sfc_client
            distribution: ubuntu
            version: 14.04


    VM2:
      type: tosca.nodes.Compute
      capabilities:
        # Host container properties
        host:
         properties:
           num_cpus: 2
           disk_size: 10 GB
           mem_size: 512 MB
        # Guest Operating System properties
        os:
          properties:
            # host Operating System image properties
            architecture: x86_64
            type: sfc_client
            distribution: ubuntu
            version: 14.04
            
    VM3:
      type: tosca.nodes.Compute
      capabilities:
        # Host container properties
        host:
         properties:
           num_cpus: 2
           disk_size: 10 GB
           mem_size: 512 MB
        # Guest Operating System properties
        os:
          properties:
            # host Operating System image properties
            architecture: x86_64
            type: sfc_client
            distribution: ubuntu
            version: 14.04

    my_network:
      type: tosca.nodes.network.Network
      properties:
        network_name: { get_input: network_name }

    my_port1:
      type: tosca.nodes.network.Port
      requirements:
        - binding:
            node: VM1
        - link:
            node: my_network

    my_port2:
      type: tosca.nodes.network.Port
      requirements:
        - binding:
            node: VM2
        - link:
            node: my_network

    my_port3:
      type: tosca.nodes.network.Port
      requirements:
        - binding:
            node: VM3
        - link:
            node: my_network
            
    VNF1:
      type: tosca.nodes.nfv.VNF
      properties:
        id: vnf1
        vendor: acmetelco
        version: 1.0
      attributes:
        type: dpi
        address: 10.100.0.105
        port: 40000
        nsh_aware: true 
      # requirements:
      #   - host: VM1

    CP11:          #endpoints of VNF1 linked to VL1
      type: tosca.nodes.nfv.CP
      properties:
      attributes:
        IP_address: 10.100.0.105
        interface: ens3
        port: 30000
      requirements:
        - virtualBinding: VNF1
        - virtualLink: VL1

    VNF2:
      type: tosca.nodes.nfv.VNF
      properties:
        id: vnf1
        vendor: acmetelco
        version: 1.0
      attributes:
        type: firewall
        address: 10.100.0.106
        port: 40000
        nsh_aware: true
      # requirements:
      #   - host: VM2


    CP21:          #endpoints of VNF2 linked to VL1
      type: tosca.nodes.nfv.CP
      properties:
      attributes:
        IP_address: 10.100.0.106
        interface: ens3
        port: 30000
      requirements:
        - virtualBinding: VNF2
        - virtualLink: VL2

    VNF3:
      type: tosca.nodes.nfv.VNF
      properties:
        id: vnf1
        vendor: acmetelco
        version: 1.0
      attributes:
        type: napt44
        address: 10.100.0.107
        port: 40000
        nsh_aware: true
      # requirements:
      #   - host: VM3


    CP31:          #endpoints of VNF3 linked to VL2
      type: tosca.nodes.nfv.CP
      properties:
      attributes:
        IP_address: 10.100.0.107
        port: 30000
        interface: ens3
      requirements:
        - virtualBinding: VNF3
        - virtualLink: VL2
    CP41:          #endpoints of VNF3 linked to VL2
      type: tosca.nodes.nfv.CP
      properties:
      attributes:
        IP_address: 10.100.0.107
        port: 30000
        interface: ens3
      requirements:
        - virtualBinding: VNF3
        - virtualLink: VL1

    VL1:
      type: tosca.nodes.nfv.VL
      properties:
        vendor: HP
      attributes:
        type: ip
        transport_type: vxlan-gpe
    VL2:
      type: tosca.nodes.nfv.VL
      properties:
        vendor: HP
      attributes:
        type: ip
        transport_type: vxlan-gpe
    VL3:
      type: tosca.nodes.nfv.VL
      properties:
        vendor: HP
      attributes:
        type: ip
        transport_type: vxlan-gpe
    


    Forwarding_path1:
      type: tosca.nodes.nfv.FP
      description: the path (CP11->CP21->CP31)
      properties:
        policy: example_policy
      requirements:
        - forwarder:
            capability: CP11
            relationship: CP21
        - forwarder:
            capability: CP21
            relationship: CP31

    Forwarding_path2:
      type: tosca.nodes.nfv.FP
      description: the path (CP11->CP21->CP31->CP21)
      properties:
        policy: example_policy
      requirements:
        - forwarder:
            capability: CP11
            relationship: CP21
        - forwarder:
            capability: CP21
            relationship: CP31
        - forwarder:
            capability: CP31
            relationship: CP11
        

  # #################################################
  # # VNF Forwarding Graph nodes and the associated 
  # # Network Forwarding Paths 
  # #################################################	


  groups:
    VNF_FG1: #NFC
      type: tosca.groups.nfv.VNFFG
      description: VNF forwarding graph
      properties:
        vendor:
        version:
        connection_point: [ CP11, CP21, CP31 ]
        dependent_virtual_link: [ VL1 ]
        constituent_vnfs: [ VNF1, VNF2, VNF3 ]
      members: [ Forwarding_path1 ]

  outputs:
    vnf1_ip:
      description: The private IP address of the VNF container1.
      value: { get_attribute: [VM1, private_address] }
    vnf2_ip:
      description: The private IP address of the VNF container2.
      value: { get_attribute: [VM2, private_address] }
    vnf3_ip:
      description: The private IP address of the VNF container3.
      value: { get_attribute: [VM3, private_address] }
```