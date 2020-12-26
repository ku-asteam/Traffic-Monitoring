from operator import attrgetter

from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

class SimpleMonitor(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(SimpleMonitor, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        file1 = open("FlowStats.txt", "w")
        file1.write('datapath, in-port, eth-dst, out-port, packets, bytes, duration-sec, length')
        file1.close()
        file2 = open("PortStats.txt", "w")
        file2.write('datapath, port, rx-pkts, rx-bytes, rx-error, tx-pkts, tx-bytes, tx-error')
        file2.close()

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        file1 = open("FlowStats.txt", "w")
        body = ev.msg.body
        self.logger.info('datapath         in-port  eth-dst           out-port packets  bytes    duration-sec length')
        self.logger.info('---------------- -------- ----------------- -------- -------- -------- ------------ --------')
        for stat in sorted([flow for flow in body if flow.priority == 1], key=lambda flow: (flow.match['in_port'], flow.match['eth_dst'])):
            self.logger.info('%016x %8x %17s %8x %8d %8d %12d %8d', ev.msg.datapatht.id, stat.match['in_port'], stat.match['eth_dst'], stat.instructions[0].actions[0].port, stat.packet_count, stat.byte_count, stat.duration_sec, stat.length)
            file1.write("\n" + str(ev.msg.datapatht.id) + "," + str(stat.match['in_port']) + "," + str(stat.match['eth_dst']) + "," + str(stat.instructions[0].actions[0].port) + "," + str(stat.packet_count) + "," + str(stat.byte_count) + "," + str(stat.duration_sec) + "," + str(stat.length))
        file1.close()

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        file2 = open("PortStats.txt", "w")
        body = ev.msg.body
        self.logger.info('datapath         port     rx-pkts  rx-bytes rx-error tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- -------- -------- -------- -------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d', ev.msg.datapatht.id, stat.port_no, stat.rx_packtets, stat.rx_bytes, stat.rx_errors, stat.tx_packtets, stat.tx_bytes, stat.tx_errors)
            file2.write("\n" + str(ev.msg.datapatht.id) + "," + str(stat.port_no) + "," + str(stat.rx_packtets) + "," + str(stat.rx_bytes) + "," + str(stat.rx_errors) + "," + str(stat.tx_packtets) + "," + str(stat.tx_bytes) + "," + str(stat.tx_errors))
