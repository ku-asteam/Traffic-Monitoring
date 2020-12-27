# Traffic Monitoring Application for RYU

## Requirements
OpenFlow를 사용해 스위치의 통계 정보를 얻는 Application. RYU의 simple_monitor App에서 다양한 통계 항목을 추가한 소스코드이며, 수집한 데이터들을 txt 파일로 저장한다.

## Requirements
스위칭 허브의 실행을 위해 OpenFlow 스위치는 Open vSwitch 실행 환경으로 mininet을 사용한다.
- Mininet
- Open vSwitch
- Ryu  
`$ sudo apt-get install git python-dev python-setuptools python-pip`  
`$ git clone https://github.com/osrg/ryu.git`  
`$ cd ryu'  
`$ sudo pip install .`

## Running
- Mininet 환경 시작
구축 환경은 호스트 3 대, 스위치 하나의 간단한 구성이다.
    $ sudo mn --topo single,3 --mac --switch ovsk --controller remote -x
실행하면 데스크탑 PC에서 5개의 xterm이 시작된다. 각 xterm은 호스트 1~3, 스위치, 그리고 컨트롤러에 대응한다.


- 스위치에 대한 xterm에서 명령을 실행하여 사용하는 OpenFlow 버전을 설정한다.
윈도우 제목이 「switch : s1 (root)」인 xterm으로 스위치용 xterm이다.
우선 Open vSwitch의 상태를 확인한다.
    switch: s1:
    root@ryu-vm:~# ovs-vsctl show
    root@ryu-vm:~# ovs-dpctl show
스위치 (브리지) s1 이 생성되었고, 호스트에 해당 포트가 3개 추가되어 있습니다.

- 다음 OpenFlow 버전을 1.3으로 설정합니다.
    switch: s1:
    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13

- 플로우 테이블을 확인해 본다.
    switch: s1:
    root@ryu-vm:~# ovs-ofctl -O OpenFlow13 dump-flows s1
ovs-ofctl 명령 실행시, 옵션으로 사용하는 OpenFlow 버전을 지정해야 한다. 기본값은 OpenFlow10 이다.

- 트래픽 모니터를 실행한다.
윈도우 제목이 「controller : c0 (root)」인 xterm에서 다음 명령을 실행한다.
    controller: c0:
    root@ryu-vm:~# ryu-manager --verbose ./traffic_monitor.py
플로우 항목이 없고, 각 포트의 개수도 모두 0이다.

- host1에서 host2로 ping을 실행한다.
    host: h1:
    root@ryu-vm:~# ping -c1 10.0.0.2
패킷 전송 및 플로우 항목이 등록되고 통계 정보가 변경된다.

- 윈도우 제목이 「controller : c0 (root)」인 xterm에서 플로우 통계 정보와 포트 통계 정보를 확인할 수 있다.



