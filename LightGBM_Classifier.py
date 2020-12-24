from operator import attrgetter

from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

import pymysql

class SimpleMonitor(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(SimpleMonitor, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.mydb = mysql.connect(host="localhost", user="root", password="ab2900014", database="sdn")
        self.mycursor = self.mydb.cursor()

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
            self._lightGBM_classification()
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
        body = ev.msg.body
        for stat in sorted([flow for flow in body if flow.priority == 1], key=lambda flow: (flow.match['in_port'], flow.match['eth_dst'])):
            sql = "INSERT into flowStats (datapath_id, in_port, eth_dst, packet_count, byte_count, duration_sec, length) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            val = (str(ev.msg.datapath.id), str(stat.match['in_port']), str(stat.match['eth_dst']), str(stat.packet_count), str(stat.byte_count), str(stat.duration_sec), str(stat.length))
            self.mycursor.execute(sql, val)
            self.mydb.commit()

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        for stat in sorted(body, key=attrgetter('port_no')):
            sql = "INSERT into portStats (datapath_id, port_no, rx_bytes, rx_packets, tx_bytes, tx_packets) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (str(ev.msg.datapath.id), str(stat.port_no), str(stat.rx_bytes), str(stat.rx_packets), str(stat.tx_bytes), str(stat.tx_packets))
            self.mycursor.execute(sql, val)
            self.mydb.commit()

    def _lightGBM_classification(self):
        mydb = mysql.connector.connect(host="localhost", user="root", passwd="ab2900014", database="sdn")
        mycursor = mydb.cursor()
        sql1 = "select * from flowStats order by id desc limit 1"
        mycursor.execute(sql1)
        row_f = mycursor.fetchall()
        sql2 = "select * from portStats order by id desc limit 1"
        mycursor.execute(sql2)
        row_p = mycursor.fetchall()

        if len(row_f)>0 and len(row_p)>0:
            flow = list(row_f[0])[:-1]
            port = list(row_p[0])[:-1]
            flow_df = pd.DataFrame([flow], columns=["datapath_id", "in_port", "eth_dst", "packet_count", "byte_count", "duration_sec", "lenght"])
            port_df = pd.DataFrame([port], columns=["datapath_id", "port_no", "rx_bytes", "rx_packets", "tx_bytes", "tx_packets"])
            df = pd.concat([flow_df, port_df], axis=1, join='inner')

            feature_list = ['in_port', 'packet_count', 'byte_count', 'duration_sec', 'length', 'port_no', 'rx_bytes', 'rx_packets', 'tx_bytes', 'tx_packets']
            df = df[feature_list]
            lightGBM_clf = joblib.load('lightGBM.pkl')
            res = lightGBM_clf.predict(df)
            print(res)