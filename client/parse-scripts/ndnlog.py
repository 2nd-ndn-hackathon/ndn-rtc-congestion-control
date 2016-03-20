# this is a module that have basic primitive classes and functions for 
# parsing NDN-RTC logs and NFD logs

import fileinput
import re
from enum import Enum

DefaultTimeFunc = lambda match: int(match.group('timestamp'))

# NDN-RTC interest/data name. 
# filters interests' and data names according to the current NDN-RTC namespace
# for example:
# /ndn/edu/ucla/remap/ndnrtc/user/clockwork_ndn/streams/camera/low/key/3991/data/%00%00/5/119730/115739/1/59709
# 
# these groups are available if regex match:
# - user - user name
# - stream - media stream name
# - thread - media thread name
# - frame_type - delta/key
# - frame_no - frame number
# - data_type - data/parity
# - seg_no - segment number (use segNoToInt function to convert canonical segment number into integer)
# - play_no - frame playback number (optional, valid for data names only, not interest names)
# - segnum - total number of segments (optional, valid for data names only)
# - psegnum - total number of parity segments (optional, valid for data names only)
# NdnRtcNameRegexString = "(/[A-z0-9_\-\+]+)+/(?P<frame_type>delta|key)/(?P<frame_no>[0-9]+)/(?P<data_type>data|parity)/(?P<seg_no>[%0-9a-fA-F]+)(/[0-9]+/(?P<play_no>[0-9]+)/(?P<segnum>[0-9]+)/(?P<psegnum>[0-9]+))?"
NdnRtcNameRegexString = "(/[A-z0-9_\-\+]+)+/(?P<user>[A-z0-9_\-\+]+)+/streams/(?P<stream>[A-z0-9_\-\+]+)+/(?P<thread>[A-z0-9_\-\+]+)+/(?P<frame_type>delta|key)/(?P<frame_no>[0-9]+)/(?P<data_type>data|parity)/(?P<seg_no>[%0-9a-fA-F]+)(/[0-9]+/(?P<play_no>[0-9]+)/(?P<segnum>[0-9]+)/(?P<psegnum>[0-9]+))?"

# statistics captions
NdnRtcStatCaptions = [
"Acquired frames", 
"Acquired key frames",
"Dropped frames",
"Dropped key frames",
"Assembled frames",
"Assembled key frames",
"Recovered frames",
"Recovered key frames",
"Rescued frames",
"Rescued key frames",
"Incomplete frames",
"Incomplete key frames",
"Jitter target size",
"Jitter playable size",
"Jitter estimated size",
"Producer rate",
"Playback #",
"Last delta #",
"Last key #",
"Played frames",
"Played key frames",
"Skipped (no key)",
"Skipped (incomplete)",
"Skipped (bad GOP)",
"Skipped (incomplete key)",
"Latency (est.)",
"Delta segments average",
"Key segments average",
"Delta parity segments average",
"Key parity segments average",
"Retransmission frequency",
"Retransmissions",
"Rebufferings",
"Requested",
"Requested key",
"Default W",
"Current W",
"RTT'",
"Incoming bitrate (Kbps)",
"Incoming segments rate",
"Segments received",
"Timeouts",
"RTT estimation",
"Interest rate",
"Interest queue",
"Sent interests"]

def getStatisticsRegexString():
	return getStatCaptionsRegexString()+'\s*(?P<value>-?[0-9]+\.[0-9]{2})'

def getStatCaptionsRegexString():
	s = '(?P<caption>'
	for c in NdnRtcStatCaptions:
		if not NdnRtcStatCaptions.index(c) == 0:
			s += '|'
		s += re.escape(str(c))
	s += ')'
	return s


def parseLog(file, actionArray):
	"""Parses file line by line and check it using action array.
	Action array's elements are dictionaries with these fields:
		pattern - 	specifies compiled regex pattern which will be 
					used for checking a line
		tfunc - 	specifies time function which is used to get 
					integer (or double) value of log time. function
					takes regex match as an argument. function is 
					invoked only when match with the pattern was 
					succesfull
		func - 		specifies function which is invoked every time 
					line matched specified regex pattern. function
					takes time and match object as arguments. if 
					function returns True - parsing continues, 
					otherwise - stops
		userData -	any user data that will be passed to the 
					function
	"""
 	timestamp = 0
 	stop = False
 	with open(file) as f:
 	    nLines = 0
 	    for line in f:
 	      for action in actionArray:
 	        pattern = action['pattern']
 	        timeFunc = action['tfunc']
 	        actionFunc = action['func']
 	        userData = None
 	        if action.has_key('userdata'):
 	        	userData = action['userdata']
 	        m = pattern.match(line)
 	        if m and actionFunc:
 	          timestamp = timeFunc(m)
 	          if not actionFunc(timestamp, m, {'userData':userData, 'lineNo':nLines}):
 	            action['func'] = None
 	            break
 	      nLines+=1
 	    # for line
 	    # print 'parsed '+str(nLines)+' lines'
# with

def getSummaryStat(logFile):
	""" Extracts final statistics from consumer log file
	Returns dictionary where key is a statistics caption defined in NdnRtcStatCaptions array
	"""
	regex = re.compile(getStatisticsRegexString())
	stopLine = compileNdnLogPattern(NdnLogToken.stat.__str__(), '.*consumer', 'final statistics:')
	summary = {}
	nLinesParsed = 0
	for line in reversed(open(logFile).readlines()):
		m = regex.match(line)
		if m:
			summary[m.group('caption')] = m.group('value')
		final = stopLine.match(line)
		if final:
			break;
		nLinesParsed += 1
	return summary

def compileNdnLogPattern(tokenString, componentString, msgRegExpString):
	"""" Compiles regular expression for parsing NDN-RTC log file
	NDN-RTC log line has certain structure:
		<timestamp>	TAB	[<log_level>][<component_name>]-<component_address>: <message>
	these fields can be accessed through match object using names from the above, i.e.
		match.group('component_address')
	"""
	patternString = '(?P<timestamp>[.0-9]+)\s?\[\s*(?P<log_level>'+tokenString+')\s*\]\s?\[\s*(?P<component_name>'+componentString+')\s*\]-\s+(?P<component_address>0x[0-9a-f]+):\s?(?P<message>.*'+msgRegExpString+'.*)'
	return re.compile(patternString)

def segNoToInt(segNo):
  """ Converts canonical segment number (string) into an integer
  """
  try:
  	return int(segNo.split("%")[1]+segNo.split("%")[2], 16)
  except:
  	print "problem segno"+str(segNo)
  	return 0

def intToSegNo(segNo):
	""" Converts integer segment number into a canonical segments number (string)
	"""
	hexs=hex(segNo).replace('0x','')
	byte1 = ''
	byte0 = ''
	i = 0
	for ch in reversed(hexs):
		if i < 2:
			byte0 = ch + byte0
		elif i < 4:
			byte1 = ch + byte1
		i+=1
	while len(byte0) != 2:
		byte0 = '0'+byte0
	while len(byte1) != 2:
		byte1 = '0'+byte1
	return '%'+byte1+'%'+byte0

# segment key string - is a string in a form of "<frame_number>-<segment_number>"
# this string uniquely identifies frame segments throughout one consumer log file
def frameNoFromSegKey(segKey):
	""" Extracts frame number from segment key string (which is usually in a form of '<frameNo>-<segNo>'') """
	divPos = segKey.find('-')
	if divPos >= 0:
		return int(segKey[0:divPos])
	else:
		raise Exception('unexpected segment key', segKey)

def segmentNoFromSegKey(segKey):
	""" Extracts segment number from segment key string (which is usually in a form of '<frameNo>-<segNo>'') """
	divPos = segKey.find('-')
	if divPos >= 0:
		return int(segKey[divPos+1:])
	else:
		raise Exception('unexpected segment key', segKey)

#******************************************************************************
class NdnLogToken(Enum):
	"""Represents available log levels for NDN-RTC log"""
	trace = 1
	debug = 2
	info = 3
	warning = 4
	error = 5
	stat = 6

	@staticmethod
	def FromString(string):
		try:
			return {'trace':NdnLogToken.trace, 'debug':NdnLogToken.debug, 'info':NdnLogToken.info, 'warn':NdnLogToken.warning, 'error':NdnLogToken.error, 'stat':NdnLogToken.stat}[str.lower(string)]
		except:
			return None		

	def __str__(self):
		return	{NdnLogToken.trace:'TRACE', NdnLogToken.debug:'DEBUG', NdnLogToken.info:'INFO', NdnLogToken.warning:'WARN', NdnLogToken.error:'ERROR', NdnLogToken.stat:'STAT'}[self]

	def __repr__(self):
		return self.__str__()

#******************************************************************************
class Frame:
  # This class can be used to parse consumer-buffer output for frame entries
  FrameStringPattern = '(?P<frameType>[K|D])\s*,\s*(?P<seqNo>-?\d+)\s*,\s*(?P<playNo>-?\d+)\s*,\s*(?P<frame_ts>-?\d+)\s*,\s*(?P<assembledLevel>-?\d+\.?\d*)%\s*\((?P<parityLevel>((-?\d*\.?\d*)|(nan)))%\)\s*,\s*(?P<pairedNo>-?\d+)\s*,\s*(?P<consistency>[CIHP]),\s*(?P<deadline>-?\d+),\s*(?P<cache_status>(ORIG|CACH)),\s*(?P<rtx_count>[0-9]+),\s*(?P<recovery_state>[I|R]),\s*(?P<total_seg>[0-9]+)/(?P<ready_seg>[0-9]+)/(?P<pending_seg>[0-9]+)/(?P<missing_seg>[0-9]+)/(?P<parity_seg>[0-9]+)\s*(?P<lifetime>[0-9]+)\s*(?P<asm_time>[0-9]+)\s*(?P<asm_size>[0-9]+)\s*(?P<mem_addr>0x[A-Fa-f0-9]+)'
  BufferFrameStringPattern = '(?P<buf_idx>[0-9]+):\s(?P<frameType>[K|D])\s*,\s*(?P<seqNo>-?\d+)\s*,\s*(?P<playNo>-?\d+)\s*,\s*(?P<frame_ts>-?\d+)\s*,\s*(?P<assembledLevel>-?\d+\.?\d*)%\s*\((?P<parityLevel>((-?\d*\.?\d*)|(nan)))%\)\s*,\s*(?P<pairedNo>-?\d+)\s*,\s*(?P<consistency>[CIHP]),\s*(?P<deadline>-?\d+),\s*(?P<cache_status>(ORIG|CACH)),\s*(?P<rtx_count>[0-9]+),\s*(?P<recovery_state>[I|R]),\s*(?P<total_seg>[0-9]+)/(?P<ready_seg>[0-9]+)/(?P<pending_seg>[0-9]+)/(?P<missing_seg>[0-9]+)/(?P<parity_seg>[0-9]+)\s*(?P<lifetime>[0-9]+)\s*(?P<asm_time>[0-9]+)\s*(?P<asm_size>[0-9]+)\s*(?P<mem_addr>0x[A-Fa-f0-9]+)'

  def __init__(self, m):
  	try:
  		self.bufIdx = int(m.group('buf_idx'))
  	except:
  		self.bufIdx = -1
  	self.frameType = m.group('frameType')
  	self.seqNo = int(m.group('seqNo'))
  	self.playNo = int(m.group('playNo'))
  	self.timestamp = int(m.group('frame_ts'))
  	self.assembledLevel = float(m.group('assembledLevel'))
  	self.parityLevel = float(m.group('parityLevel'))
  	self.pairedNo = int(m.group('pairedNo'))
  	self.consistency = m.group('consistency')
  	self.deadline = int(m.group('deadline'))
  	self.cacheStatus = m.group('cache_status')
  	self.rtxCount = int(m.group('rtx_count'))
  	self.recoveryState = m.group('recovery_state')
  	self.totalSeg = int(m.group('total_seg'))
  	self.readySeg = int(m.group('ready_seg'))
  	self.pendingSeg = int(m.group('pending_seg'))
  	self.missing_seg = int(m.group('missing_seg'))
  	self.paritySeg = int(m.group('parity_seg'))
  	self.lifetime = int(m.group('lifetime'))
  	self.asmTime = int(m.group('asm_time'))
  	self.asmSize = int(m.group('asm_size'))
  	self.memAddress = m.group('mem_addr')

  @staticmethod
  def initFromString(string):
    pat =".*("+Frame.FrameStringPattern+").*"
    pattern = re.compile(pat)
    m = pattern.match(string)
    f = None
    if m:
      f = Frame(m)
    return f
  
  def __str__(self):
      return "["+str(self.frameType)+", "+str(self.seqNo)+", "+str(self.playNo)+", "+str(self.timestamp)+", "+str(self.assembledLevel)+"% ("+str(self.parityLevel)+"%), "+str(self.pairedNo)+", "+str(self.consistency)+', '+str(self.deadline)+', '+str(self.rtxCount)+', '+str(self.cacheStatus)+"]"
  
  def __repr__(self):
      return self.__str__()

#******************************************************************************
class BufferState:
	""" This class represents buffer state printed in consumer log file
	"""
	def __init__(self):
		self.frames = []

	def addFrame(self, timestamp, frame):
		if not len(self.frames):
			self.timestamp = timestamp
		self.frames.append(frame)

	def __str__(self):
		if len(self.frames):
			s = str(self.timestamp)+' '+str(len(self.frames))+' frames:\n'
			i = 0
			for frame in self.frames:
			  s += str(i)+'\t'+str(frame) + '\n'
			  i += 1
			return s
		return "<empty_buffer>"
