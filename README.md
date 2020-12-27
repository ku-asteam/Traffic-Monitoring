# Traffic Monitoring Application for RYU    
Application that uses OpenFlow to obtain statistical information of the switch. A source code for adding a variety of statistical features from the simple monitor application of the RYU, which stores the collected data in a txt file.  
## Requirements  
For execution, OpenFlow switches use Mininet as an Open vSwitch execution environment.  
- Mininet  
- Open vSwitch  
- Ryu  
`$ sudo apt-get install git python-dev python-setuptools python-pip`  
`$ git clone https://github.com/osrg/ryu.git`  
`$ cd ryu`  
`$ sudo pip install .`  
## Running  
**1. Set topology**  
The deployment environment is a simple configuration of three hosts, one switch.  
`$ sudo mn --topo single,3 --mac --switch ovsk --controller remote -x`  
When executed, five xterms are started. Each xterm corresponds to a host 1-3, switch, and controller.  

**2. Check the status of the Open vSwitch.**  
It is xterm for switches with the title 「switch : s1 (root)」.   
**switch: s1:**  
`root@ryu-vm:~# ovs-vsctl show`  
`root@ryu-vm:~# ovs-dpctl show`  
Make sure that switch (bridge) s1 is created and that the host has three additional corresponding ports.  

**3. Set the OpenFlow version to 1.3.**  
Set the OpenFlow version by running the command in xterm for the switch.  
**switch: s1:**  
`root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13`  

**4. Check the flow table.**  
**switch: s1:**  
`root@ryu-vm:~# ovs-ofctl -O OpenFlow13 dump-flows s1`  
When executing the 'ovs-ofctl' command, you must specify the version of OpenFlow. The default is OpenFlow10.  

**5. Run the traffic monitor.**  
Run the following command in xterm with the window title「controller : c0 (root)」.  
**controller: c0:**  
`root@ryu-vm:~# ryu-manager --verbose ./traffic_monitor.py`  
There are no flow entries, and the number of each port is also zero.  

**6. Ping host1 to host2.**  
**host: h1:**  
`root@ryu-vm:~# ping -c1 10.0.0.2`  
Packet transmission and flow entries are registered and statistical information is changed.  

**7. Flow and port statistical information can be found in xterm with the window title 「controller : c0 (root)」.**  
