#!/usr/bin/env python

import ndnlog
import sys
from ndnlog import NdnLogToken
from enum import Enum
from collections import OrderedDict
import re

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
  unstable = 15
  lowBuf = 16
  lambdaMin = 17
  lambdaMax = 18
  unknown = 99

  def __str__(self):
    return {StatKeyword.Dgen:'Dgen_ms', StatKeyword.Darr:'Darr_ms',\
      StatKeyword.bufTarget:'buf_tar_ms', StatKeyword.bufEstimate:'buf_est_ms', StatKeyword.bufPlayable:'buf_play_ms',\
      StatKeyword.rttEst:'rtt_est_ms', StatKeyword.rttPrime:'rtt_prime_ms',\
      StatKeyword.lambdaD:'lambda_d', StatKeyword.lambdaC:'lambda',\
      StatKeyword.rtx:'rtx_total', StatKeyword.rescued:'rescued_total', StatKeyword.recovered:'recovered_total',
      StatKeyword.lat:'lat_est_sec', StatKeyword.rttVar:'rtt_var', StatKeyword.unknown:'unknown',
      StatKeyword.lowBuf:'low_buf', StatKeyword.unstable:'unstable',
      StatKeyword.lambdaMin:'lambda_min', StatKeyword.lambdaMax:'lambda_max'}[self]

statKeywordToEntryMap = {StatKeyword.Dgen:'Dgen', StatKeyword.Darr:'Darr',\
    StatKeyword.bufTarget:'buf tar', StatKeyword.bufEstimate:'buf est', StatKeyword.bufPlayable:'buf play',\
    StatKeyword.rttEst:'rtt est', StatKeyword.rttPrime:'rtt prime raw',\
    StatKeyword.lambdaD:'lambda_d', StatKeyword.lambdaC:'lambda',\
    StatKeyword.rtx:'rtx', StatKeyword.rescued:'resc', StatKeyword.recovered:'recover',
    StatKeyword.lat:'lat est', StatKeyword.rttVar:'rtt var',
    StatKeyword.lowBuf:'low_buf', StatKeyword.unstable:'unstable',
    StatKeyword.lambdaMin:'lambda_min', StatKeyword.lambdaMax:'lambda_max'}
statEntryToKeywordMap = {v: k for k, v in statKeywordToEntryMap.items()}

def statKeywordToEntry(kw):
  global statKeywordToEntryMap
  return statKeywordToEntryMap[kw]

def statEntryToKeyword(stat):
  global statEntryToKeywordMap
  if not stat in statEntryToKeywordMap.keys(): return StatKeyword.unknown
  return statEntryToKeywordMap[stat]

statRegexString = '(?P<stat_entry>'+statKeywordToEntry(StatKeyword.Dgen)+'|'+statKeywordToEntry(StatKeyword.Darr)+'|'+\
  statKeywordToEntry(StatKeyword.bufTarget)+'|'+statKeywordToEntry(StatKeyword.bufEstimate)+'|'+statKeywordToEntry(StatKeyword.bufPlayable)+'|'+\
  statKeywordToEntry(StatKeyword.rttEst)+'|'+statKeywordToEntry(StatKeyword.rttPrime)+'|'+\
  statKeywordToEntry(StatKeyword.lambdaD)+'|'+\
  statKeywordToEntry(StatKeyword.recovered)+'|'+statKeywordToEntry(StatKeyword.rescued)+'|'+statKeywordToEntry(StatKeyword.rtx)+'|'+\
  statKeywordToEntry(StatKeyword.lowBuf)+'|'+statKeywordToEntry(StatKeyword.unstable)+'|'+\
  statKeywordToEntry(StatKeyword.lambdaMin)+'|'+statKeywordToEntry(StatKeyword.lambdaMax)+'|'+\
  statKeywordToEntry(StatKeyword.lat)+')\\t(?P<value>[0-9.-]+)'

statRegex = re.compile(statRegexString)

def closeStatBlock(timestamp):
  global statBlock, runBlock, interestNo, dataNo, runNo, statBlockNum, inceptionTimestamp
  global inceptionPacket, lastCloseTimestamp
  # write header
  if lastCloseTimestamp == timestamp: return
  if statBlockNum == 0 and noHeaders:
    sys.stdout.write('unix_ts_ms\trts_ms\trun\tint_seq\trelative_int_seq\tdata_seq\trelative_data_seq\t')
    for key in statBlock.keys():
      sys.stdout.write(str(key))
      if statBlock.keys().index(key) != len(statBlock.keys())-1:
        sys.stdout.write('\t')
    sys.stdout.write('\n')
  # write common stat
  if noHeaders:
    rts = (timestamp-inceptionTimestamp) if inceptionTimestamp != 0 else 0
    rint = (interestNo-inceptionPacket) if inceptionPacket != 0 and interestNo > 0 else 0
    rdata = (dataNo-inceptionPacket) if inceptionPacket != 0 else 0
    sys.stdout.write(str(timestamp)+'\t'+str(rts)+'\t'+str(runNo)+'\t'+str(interestNo)+'\t'+\
      str(rint)+'\t'+str(dataNo)+'\t'+str(rdata)+'\t')
  # write detailed stat
  for key in statBlock.keys():
    value = statBlock[key]
    # mean = sum(values, 0.0) / len(values) if len(values) > 0 else 0
    if noHeaders:
      sys.stdout.write(str(value))
      # sys.stdout.write(str(mean))
      if statBlock.keys().index(key) != len(statBlock.keys())-1:
        sys.stdout.write('\t')
    # if mean != 0: runBlock[key].append(mean)
    # statBlock[key] = [values[len(values)-1]] if len(values) else []
  sys.stdout.write('\n')
  statBlockNum += 1
  lastCloseTimestamp = timestamp

def closeRun(timestamp):
  global summaryFile, runClosed
  global runNo, runBlock, lastTimestamp, runStartTime, chaseTime
  closeStatBlock(timestamp)
  # if summaryFile:
  #   with open(summaryFile, "a") as f:
  #     f.write('run '+str(runNo)+'\tts\t'+str(timestamp)+'\tchase time\t'+str(chaseTime)+'\trun time\t'+str(lastTimestamp-runStartTime)+'\t')
  #     for key in runBlock.keys():
  #       values = runBlock[key]
  #       mean = sum(values, 0.0) / len(values) if len(values) > 0 else 0
  #       f.write(key+'\t'+str(mean)+'\t')
  #       runBlock[key] = []
  #       statBlock[key] = []
  #     f.write('\n')
  # else:
  #   print "*** run summary"
  #   sys.stdout.write('ts\t'+str(timestamp)+'\trun '+str(runNo)+'\tchase time\t'+str(chaseTime)+'\trun time\t'+str(lastTimestamp-runStartTime)+'\t')
  #   for key in runBlock.keys():
  # 	 values = runBlock[key]
  # 	 mean = sum(values, 0.0) / len(values) if len(values) > 0 else 0
  # 	 sys.stdout.write(key+'\t'+str(mean)+'\t')
  # 	 runBlock[key] = []
  # 	 statBlock[key] = []
  #   sys.stdout.write('\n')
  #   print "***"
  runNo += 1
  runClosed = True

def timeFunc(match):
  global timeSlice, inceptionTimestamp
  global lastTimestamp, runClosed, runStartTime, chaseTime
  timestamp = int(match.group('timestamp'))
  if (inceptionTimestamp == 0): inceptionTimestamp = timestamp
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
  	# closeStatBlock(timestamp)
  	lastTimestamp = timestamp
  return timestamp

def onRebuffering(timestamp, match, userData):
  closeRun(timestamp)
  return True

def onInterest(timestamp, match, userData):
  global interestNo, inceptionPacket
  interestNo = int(match.group('frame_no'))
  if inceptionPacket == 0: inceptionPacket = int(interestNo)
  closeStatBlock(timestamp)
  return True

def onData(timestamp, match, userData):
  global dataNo, inceptionPacket
  dataNo = int(match.group('frame_no'))
  if inceptionPacket == 0: inceptionPacket = int(dataNo)
  closeStatBlock(timestamp)
  return True

def onChasingPhaseEnded(timestamp, match, userData):
  global runStartTime, chaseTime
  chaseTime = match.group('chase_time')
  #print "chase in "+str(chaseTime)
  return True

def onStatEntry(timestamp, match, userData):
  global statBlock, lastTimestamp
  shouldCloseBlock = False
  for m in statRegex.finditer(match.group('message')):
    statEntry = m.group('stat_entry')
    statKeyword = statEntryToKeyword(statEntry)
    value = float(m.group('value'))
    if not statKeyword in statBlock.keys():
      print match.string + '|' + statEntry + ' is not in stat block: '+str(statBlock.keys())
    else:
      # statBlock[statKeyword].append(value)
      shouldCloseBlock = (statBlock[statKeyword] != value)
      statBlock[statKeyword] = value
  if shouldCloseBlock: closeStatBlock(timestamp)
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

  inceptionTimestamp = 0
  inceptionPacket = 0
  runNo = 0
  lastCloseTimestamp = 0
  lastTimestamp = 0
  interestNo = 0
  dataNo = 0
  chaseTime = 0
  runStartTime = 0
  runClosed = False
  statBlockNum = 0

  # runBlock = OrderedDict([(str(StatKeyword.Dgen),[]), (str(StatKeyword.Darr),[]), (str(StatKeyword.bufTarget),[]), (str(StatKeyword.bufEstimate),[]),\
  # (str(StatKeyword.bufPlayable),[]), (str(StatKeyword.rttEst),[]), (str(StatKeyword.rttPrime),[]), (str(StatKeyword.lambdaD),[]), (str(StatKeyword.lambdaC),[]),\
  # (str(StatKeyword.rtx), []), (str(StatKeyword.recovered), []), (str(StatKeyword.rescued), []), (str(StatKeyword.lat), [])])

  runBlock = OrderedDict([(StatKeyword.Dgen,0.), (StatKeyword.Darr,0.), (StatKeyword.bufTarget,0), (StatKeyword.bufEstimate,0),\
  (StatKeyword.bufPlayable,0), (StatKeyword.rttEst, 0), (StatKeyword.rttPrime,0), (StatKeyword.lambdaD,0), \
  (StatKeyword.rtx, 0), (StatKeyword.recovered, 0), (StatKeyword.rescued, 0), (StatKeyword.lat, 0), \
  (StatKeyword.unstable, 0), (StatKeyword.lowBuf, 0), (StatKeyword.lambdaMin, 0), (StatKeyword.lambdaMax, 0)])
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


