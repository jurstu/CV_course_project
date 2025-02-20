import json
from datetime import datetime
import datetime as dt
import time

from influxConnector import InfluxConnector


def is_date_in_range(input_date, start_date, end_date):
   return start_date <= input_date <= end_date

class EventFilter:
    def __init__(self, eventCollector=None):
        if(eventCollector == None):
            self.eventCollector = EventCollector()
        else:
            self.eventCollector = eventCollector

    def getLast10Minutes(self, now=None, then=None):
        if(now == None):
            now = datetime.now()
        if(then == None):
            then = now - dt.timedelta(minutes=10)

        outputEvents = []
        for event in self.eventCollector.eventDict["finishedTrack"]:
            eventTime = self.eventCollector.getDatetimeFromString(event["time"])
            if(is_date_in_range(eventTime, then, now) and event["dist"] > 300):
                outputEvents.append(event)

        return outputEvents





class EventCollector:
    def __init__(self,):
        self.lastStoreTime = 0
        self.restore()
        self.eventFilter = EventFilter(self)
        self.removeDelta = dt.timedelta(hours=24)
        self.ic = InfluxConnector()
        self.lastMinute = datetime.now().minute
        self.counter = 0

    def removeOldEvents(self):
        
        for eventName in self.eventDict:
            rm = []
            for localEvents in range(len(self.eventDict[eventName])):

                t = self.getDatetimeFromString(self.eventDict[eventName][localEvents]["time"])
                now = datetime.now()
                if(t < (now - self.removeDelta)):
                    rm.append(localEvents)
                if("path" in self.eventDict[eventName][localEvents]):
                    del self.eventDict[eventName][localEvents]["path"]
            out = []
            for i, el in enumerate(self.eventDict[eventName]):
                if(i not in rm):
                    out.append(self.eventDict[eventName][i])
            
            if(eventName != "carDetection"):
                self.eventDict[eventName] = out
            else:
                del self.eventDict[eventName]

    def registerEvent(self, eventName, additionalInfo):
        
        if(additionalInfo["dist"] > 300):
            self.counter+=1
            print("adding 1 to counter")


    def maybePush(self):
        minute = datetime.now().minute
        if(minute != self.lastMinute):
            print("pushing", self.counter)
            self.lastMinute = minute
            self.ic.pushEvent("minutely", self.counter)
            self.counter = 0





        return 
        if eventName in self.eventDict:
            self.eventDict[eventName].append(additionalInfo)
        else:
            self.eventDict[eventName] = [additionalInfo]
        self.store()

        #movements = self.eventFilter.getLast10Minutes()
        #print("number of tracked cars last 10 minutes", len(movements))

    def getDatetimeFromString(self, s):
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

    def getTimestamp(self):
        return datetime.now().strftime('%04Y-%02m-%02d %02H:%02M:%02S')


    def store(self, force=False):
        if(force or (time.time() - self.lastStoreTime > 60)):
            self.removeOldEvents()
            with open("store.json", "w") as f:
                output = json.dumps(self.eventDict, indent=4)
                f.write(output)
            self.lastStoreTime = time.time()
        
    def restore(self):
        try:
            with open("store.json", "r") as f:
                d = f.read()
                self.eventDict = json.loads(d)
        except:
            self.eventDict = {}