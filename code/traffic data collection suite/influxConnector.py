

import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS





class InfluxConnector:
    def __init__(self):
        self.token = "XXPKUPLJIHQ8xkHaYUN2LHoM_L7OQTXknPj-6_JLbpq3fuFd4igFykrLUqIFGRXx9GioEr5Lc-Fc5qDOrTs05w=="
        self.org = "Hallotron"
        self.url = "http://192.168.10.240:8086"

    def pushEvent(self, eventName, data):
        client = influxdb_client.InfluxDBClient(url=self.url, token=self.token, org=self.org)
        bucket="cars"
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = (
            Point("measurement1")
            .tag("tagname1", "tagvalue1")
            .field("field1", data)
        )
        write_api.write(bucket=bucket, org="Hallotron", record=point)


