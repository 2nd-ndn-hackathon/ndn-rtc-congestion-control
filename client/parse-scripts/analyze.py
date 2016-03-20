#!/usr/bin/env python

import ndnlog
import sys
from ndnlog import NdnLogToken
from enum import Enum
from collections import OrderedDict
import re

inceptionTimestamp = None

class StatKeyword(Enum):
  Dgen = 1
  Darr = 2
  bufTarget = 3
  bufEstimate = 4
  bufPlayable = 5
  rttEst = 6
  rttPrime = 7
  lambdaD = 8
  lambdaC = 9
  recovered = 10
  rescued = 11
  rtx = 12
  lat = 13
  rttVar = 14

  def __str__(self):
    return {StatKeyword.Dgen:'Dgen', StatKeyword.Darr:'Darr',\
    StatKeyword.bufTarget:'buf tar', StatKeyword.bufEstimate:'buf est', StatKeyword.bufPlayable:'buf play',\
    StatKeyword.rttEst:'rtt est', StatKeyword.rttPrime:'rtt prime',\
    StatKeyword.lambdaD:'lambda d', StatKeyword.lambdaC:'lambda',\
    StatKeyword.rtx:'rtx', StatKeyword.rescued:'resc', StatKeyword.recovered:'recover',
    StatKeyword.lat:'lat est', StatKeyword.rttVar:'rtt var'}[self]

def statEntryRegex(statEntry):
  return str(statEntry)

statRegexString = '(?P<stat_entry>'+statEntryRegex(StatKeyword.Dgen)+'|'+statEntryRegex(StatKeyword.Darr)+'|'+\
  statEntryRegex(StatKeyword.bufTarget)+'|'+statEntryRegex(StatKeyword.bufEstimate)+'|'+statEntryRegex(StatKeyword.bufPlayable)+'|'+\
  statEntryRegex(StatKeyword.rttEst)+'|'+statEntryRegex(StatKeyword.rttPrime)+'|'+\
  statEntryRegex(StatKeyword.lambdaD)+'|'+statEntryRegex(StatKeyword.lambdaC)+'|'+\
  statEntryRegex(StatKeyword.recovered)+'|'+statEntryRegex(StatKeyword.rescued)+'|'+statEntryRegex(StatKeyword.rtx)+'|'+\
  statEntryRegex(StatKeyword.lat)+'|'+statEntryRegex(StatKeyword.rttVar)+')\\t(?P<value>[0-9.-]+)'
statRegex = re.compile(statRegexString)

def closeStatBlock(timestamp):
  global statBlock, runBlock, interestNo, dataNo, runNo, statBlockNum, inceptionTimestamp
  # write header
  if statBlockNum == 0 and noHeaders:
    sys.stdout.write('ts\trts\trun\tint\tdata\t')
    for key in statBlock.keys():
      sys.stdout.write(key)
      if statBlock.keys().index(key) != len(statBlock.keys())-1:
        sys.stdout.write('\t')
    sys.stdout.write('\n')
  # write common stat
  if noHeaders:
    sys.stdout.write(str(timestamp)+'\t'+str(timestamp-inceptionTimestamp)+'\t'+str(runNo)+'\t'+str(interestNo)+'\t'+str(dataNo)+'\t')
  else:
    sys.stdout.write('ts\t'+str(timestamp)+'\trun\t'+str(runNo)+'\tint\t'+str(interestNo)+'\tdata\t'+str(dataNo)+'\t')
  # write detailed stat
  for key in statBlock.keys():
    values = statBlock[key]
    mean = sum(values, 0.0) / len(values) if len(values) > 0 else 0
    if noHeaders:
      sys.stdout.write(str(mean))
      if statBlock.keys().index(key) != len(statBlock.keys())-1:
        sys.stdout.write('\t')
    else:
      sys.stdout.write(key+'\t'+str(mean)+'\t')
    if mean != 0: runBlock[key].append(mean)
    statBlock[key] = [values[len(values)-1]] if len(values) else []
  sys.stdout.write('\n')
  statBlockNum += 1

def closeRun(timestamp):
  global summaryFile, runClosed
  global runNo, runBlock, lastTimestamp, runStartTime, chaseTime
  closeStatBlock(timestamp)
  if summaryFile:
    with open(summaryFile, "a") as f:
      f.write('run '+str(runNo)+'\tts\t'+str(timestamp)+'\tchase time\t'+str(chaseTime)+'\trun time\t'+str(lastTimestamp-runStartTime)+'\t')
      for key in runBlock.keys():
        values = runBlock[key]
        mean = sum(values, 0.0) / len(values) if len(values) > 0 else 0
        f.write(key+'\t'+str(mean)+'\t')
        runBlock[key] = []
        statBlock[key] = []
      f.write('\n')
  else:
    print "*** run summary"
    sys.stdout.write('ts\t'+str(timestamp)+'\trun '+str(runNo)+'\tchase time\t'+str(chaseTime)+'\trun time\t'+str(lastTimestamp-runStartTime)+'\t')
    for key in runBlock.keys():
  	 values = runBlock[key]
  	 mean = sum(values, 0.0) / len(values) if len(values) > 0 else 0
  	 sys.stdout.write(key+'\t'+str(mean)+'\t')
  	 runBlock[key] = []
  	 statBlock[key] = []
    sys.stdout.write('\n')
    print "***"
  runNo += 1
  runClosed = True

def timeFunc(match):
  global timeSlice, inceptionTimestamp
  global lastTimestamp, runClosed, runStartTime, chaseTime
  timestamp = int(match.group('timestamp'))
  if (inceptionTimestamp == None): inceptionTimestamp = timestamp
  if runClosed:
    if summaryFile:
      with open(summaryFile, "a") as f:
        f.write("recovery time\t" + str(timestamp-lastTimestamp)+"\n")
    else:
      print "recovery time\t"+str(timestamp-lastTimestamp)
    runStartTime = timestamp
    runClosed = False
    chaseTime = 0
  if lastTimestamp == 0:
  	lastTimestamp = timestamp
  if runStartTime == 0:
    runStartTime = timestamp
  if timestamp-lastTimestamp >= timeSlice:
  	closeStatBlock(timestamp)
  	lastTimestamp = timestamp
  return timestamp

def onRebuffering(timestamp, match, userData):
  closeRun(timestamp)
  return True

def onInterest(timestamp, match, userData):
  global interestNo
  interestNo = match.group('frame_no')
  return True

def onData(timestamp, match, userData):
  global dataNo
  dataNo = match.group('frame_no')
  return True

def onChasingPhaseEnded(timestamp, match, userData):
  global runStartTime, chaseTime
  chaseTime = match.group('chase_time')
  #print "chase in "+str(chaseTime)
  return True

def onStatEntry(timestamp, match, userData):
  global statBlock, lastTimestamp
  for m in statRegex.finditer(match.group('message')):
    statEntry = m.group('stat_entry')
    value = float(m.group('value'))
    if not statEntry in statBlock.keys():
      print str(statEntry) + ' is not in stat block: '+str(statBlock)
    else:
      statBlock[statEntry].append(value)
  return True

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print "usage: "+__file__+" <log_file> <timeslice_ms> [<summary_file>] [--no-headers]"
    exit(1)
  logFile = sys.argv[1]
  timeSlice = int(sys.argv[2])
  summaryFile = None
  if len(sys.argv) > 3:
    summaryFile = sys.argv[3]
  noHeaders = False
  if "--no-headers" in sys.argv:
    noHeaders = True

  runNo = 0
  lastTimestamp = 0
  interestNo = 0
  dataNo = 0
  chaseTime = 0
  runStartTime = 0
  runClosed = False
  statBlockNum = 0
  runBlock = OrderedDict([(str(StatKeyword.Dgen),[]), (str(StatKeyword.Darr),[]), (str(StatKeyword.bufTarget),[]), (str(StatKeyword.bufEstimate),[]),\
  (str(StatKeyword.bufPlayable),[]), (str(StatKeyword.rttEst),[]), (str(StatKeyword.rttPrime),[]), (str(StatKeyword.lambdaD),[]), (str(StatKeyword.lambdaC),[]),\
  (str(StatKeyword.rtx), []), (str(StatKeyword.recovered), []), (str(StatKeyword.rescued), []), (str(StatKeyword.lat), []), (str(StatKeyword.rttVar), [])])
  statBlock = runBlock.copy()

  chaseTrackRegexString = 'phase Chasing finished in (?P<chase_time>[0-9]+) msec'
  chaseTrackActions = {}
  chaseTrackActions['pattern'] = ndnlog.compileNdnLogPattern(NdnLogToken.info.__str__(), '.consumer-pipeliner', chaseTrackRegexString)
  chaseTrackActions['tfunc'] = ndnlog.DefaultTimeFunc
  chaseTrackActions['func'] = onChasingPhaseEnded

  interestExpressRegex  = 'express\t'+ndnlog.NdnRtcNameRegexString
  interestExpressActions = {}
  interestExpressActions['pattern'] = ndnlog.compileNdnLogPattern(NdnLogToken.debug.__str__(), '.iqueue', interestExpressRegex)
  interestExpressActions['tfunc'] = ndnlog.DefaultTimeFunc
  interestExpressActions['func'] = onInterest

  dataReceivedRegex  = 'data '+ndnlog.NdnRtcNameRegexString
  dataReceivedActions = {}
  dataReceivedActions['pattern'] = ndnlog.compileNdnLogPattern(NdnLogToken.debug.__str__(), '.consumer-pipeliner', dataReceivedRegex)
  dataReceivedActions['tfunc'] = ndnlog.DefaultTimeFunc
  dataReceivedActions['func'] = onData

  rebufferingRegexString = 'rebuffering #(?P<rebuf_no>[0-9]+) seed (?P<seed>[0-9]+) key (?P<key>[0-9]+) delta (?P<delta>[0-9]+) curent w (?P<cur_w>[0-9-]+) default w (?P<default_w>[0-9-]+)'
  rebufferingActions = {}
  rebufferingActions['pattern'] = ndnlog.compileNdnLogPattern(NdnLogToken.warning.__str__(), '.consumer-pipeliner', rebufferingRegexString)
  rebufferingActions['tfunc'] = timeFunc
  rebufferingActions['func'] = onRebuffering

  statEntryActions = {}
  statEntryActions['pattern'] = ndnlog.compileNdnLogPattern('.*', '.*', statRegexString)
  statEntryActions['tfunc'] = timeFunc
  statEntryActions['func'] = onStatEntry

  if summaryFile:
    with open(summaryFile, "w") as f:
      f.write("***"+logFile+"\n")
  ndnlog.parseLog(logFile, [statEntryActions, chaseTrackActions, interestExpressActions, dataReceivedActions, rebufferingActions])
  closeRun(lastTimestamp)


