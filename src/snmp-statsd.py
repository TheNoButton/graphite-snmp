#!/usr/bin/env python
# GET Command Generator
from pysnmp.entity.rfc3413.oneliner import cmdgen
import time    #could be used if modified for graphite
import socket
import re
import sys

statsdAddr = ('graph.example.edu',8125)

squid3Template = {
    'sysPageFaults'           : '1.3.6.1.4.1.3495.1.3.1.1',
    'sysNumReads'             : '1.3.6.1.4.1.3495.1.3.1.2',
    'memUsage'                : '1.3.6.1.4.1.3495.1.3.1.3',
    'cpuTime'                 : '1.3.6.1.4.1.3495.1.3.1.4',
    'cpuUsage'                : '1.3.6.1.4.1.3495.1.3.1.5',
    'maxResSize'              : '1.3.6.1.4.1.3495.1.3.1.6',
    'unusedFDescrCnt'         : '1.3.6.1.4.1.3495.1.3.1.10',
    'serverErrors'            : '1.3.6.1.4.1.3495.1.3.2.1.11',
    'clients'                 : '1.3.6.1.4.1.3495.1.3.2.1.15',
    'protoClientHttpRequests' : '1.3.6.1.4.1.3495.1.3.2.1.1',
    'httpAllSvcTime'          : '1.3.6.1.4.1.3495.1.3.2.2.1.2',
    'dnsSvcTime'              : '1.3.6.1.4.1.3495.1.3.2.2.1.8',
}

snmpConfig = [
        {
            'name' : 'iso-clientproxy-3128',  #sent in metric, e.g. stats.gauges.snmp.iso-clientproxy-3128.clients.0
            'target' : '127.0.0.1',           #snmp client address
            'community' : 'public',
            'templates' : [squid3Template],   #oids to walk
            'port' : 3401                     #optional alternate port
        },
        {
            'name' : 'iso-clientproxy-3129',
            'target' : '127.0.0.1',
            'community' : 'public',
            'templates' : [squid3Template],
            'port' : 3402
        },
        {
            'name' : 'iso-clientproxy-3130',
            'target' : '127.0.0.1',
            'community' : 'public',
            'templates' : [squid3Template],
            'port' : 3403
        },
        {
            'name' : 'iso-clientproxy-3131',
            'target' : '127.0.0.1',
            'community' : 'public',
            'templates' : [squid3Template],
            'port' : 3404
        },
    ]
        

def snmp_walk(snmpTarget, snmpCommunity, plainOID, snmpPort=161):
    cmdGen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
        cmdgen.CommunityData(snmpCommunity),
        cmdgen.UdpTransportTarget((snmpTarget, snmpPort)),
        plainOID
        )

    if errorIndication:
        print errorIndication, 'at', snmpTarget, plainOID       
        sys.exit(1)

    if errorStatus:
        print '%s at %s\n' % (
            errorStatus.prettyPrint(),
            errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
            )
        sys.exit(1)

    return varBindTable



for config in snmpConfig:
    snmpTarget = config['target']
    snmpCommunity = config['community']
    snmpPort = 161  #snmp's well-known port
    if 'port' in config:
        snmpPort = config['port']  #use custom, if specified

    records = []
    for template in config['templates']:

        for snmpName, snmpOid in template.iteritems():
            dataTable = snmp_walk(snmpTarget, snmpCommunity, snmpOid, snmpPort)

            if(dataTable is None or not dataTable):
               #print "DEBUG empty table snmpName=%s, snmpOid=%s" % (snmpName,snmpOid)
               pass

            for row in dataTable:
               for objectName, objectVal in row:
                    #print "DEBUG evaluating snmpName=%s, snmpOid=%s, objectName=%s, objectVal=%s" % (snmpName,snmpOid,objectName,objectVal)
                                  
                    metricName =  "snmp"
                    metricName +=  "." + re.sub('\s', '_', config['name'])
                    metricName +=  "." + re.sub('\s', '_', snmpName)
                    metricName +=  "." + str(objectName[-1]) #last number of oid, useful in walks
                    #sending all metrics as gauges for now...
                    record = '%s:%d|g' % (metricName, objectVal)
                    #graphite would be:
                    #record = '%s %d %d' % (metricName, objectVal, int(time.time()))
                    records.append(record)

    statsdSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    for record in records:
        #TO DO:  build payload upto MTU, then send
        print "DEBUG:", record
        statsdSocket.sendto(record,statsdAddr)
