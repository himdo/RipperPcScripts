from multiprocessing import Process
import random
import subprocess, time, os, sys, threading

# Main Configs
backupLocation = "/hdd/"
minTime = 60*60 # this is in seconds; so it reads for parts that are larger then 1 hour by default
refreshTrayTimerTime = 60 * 3 # This is in seconds; used for solving auto closing dvd trays

textColorDatabase = [
	'\x1b[0;30;41m',
	'\x1b[0;30;42m',
	'\x1b[0;30;43m',
	'\x1b[0;30;44m',
	'\x1b[0;30;45m',
	'\x1b[0;30;46m',
	'\x1b[0;30;47m',
	'\x1b[0m',
]

def printColor(text, number):
	print(textColorDatabase[number] + text + textColorDatabase[len(textColorDatabase)-1])

def _isTrayHelper(dvdLocation, lookingText):
	# used as base for all tray status functions
	cmd = ["setcd", "-i", "/dev/{}".format(dvdLocation)]
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output = []
	for line in iter(p.stdout.readline, b''):
		output.append(line.rstrip())
	return (lookingText in str(output[1]))

def isTrayOpen(dvdLocation):
	#the tray is open
	return _isTrayHelper(dvdLocation, 'CD tray is open')

def isTrayEmpty(dvdLocation):
	# the tray is currently empty
	return _isTrayHelper(dvdLocation, 'No disc is inserted')

def isTrayNotReady(dvdLocation):
	# tray is currently busy with determining if there is a disc in it
	# it is not ready right after closing the tray
	return _isTrayHelper(dvdLocation, 'Drive is not ready')

def isTrayHaveDVD(dvdLocation):
	# Found a dvd with the given location
	 return _isTrayHelper(dvdLocation, 'Disc found in drive')

def waitUntilReady(dvdLocation):
	# Waits until the tray is ready to be used
	# This is used as a way to wait to see if
	# a tray has a dvd or not after closing the tray
	notReady = isTrayNotReady(dvdLocation)
	while (notReady):
		time.sleep(1)
		notReady = isTrayNotReady(dvdLocation)

def refreshTrayTime(dvdLocation, childCount):
	# toggle the tray state twice at given dvdlocation
	# this is used as a way to reset the auto close time
	# when the tray is openned
	# has no use when tray is closed
	if isTrayOpen(dvdLocation):
		os.popen("eject -t {}".format(dvdLocation))
		time.sleep(10)
		os.popen("eject {}".format(dvdLocation))
	else:
		printColor("{} attempted to refresh tray time while not being opened".format(dvdLocation), childCount)

def openTray(dvdLocation):
	# open the dvd tray at the given location
	os.popen("eject {}".format(dvdLocation))

def closeTray(dvdLocation):
	# close the dvd tray at the given location
	os.popen("eject -t {}".format(dvdLocation))

def dvdTester(dvdLocation, childCount):
	# This is a testing function used for debuging the tray
	if isTrayOpen(dvdLocation):
		printColor("{} is Open".format(dvdLocation), childCount)
	if isTrayEmpty(dvdLocation):
		printColor("{} is Empty".format(dvdLocation), childCount)
	if isTrayNotReady(dvdLocation):
		printColor("{} is Not Ready".format(dvdLocation), childCount)
		waitUntilReady(dvdLocation)
		if isTrayEmpty(dvdLocation):
			printColor("{} is Empty".format(dvdLocation), childCount)
		elif isTrayHaveDVD(dvdLocation):
			printColor("{} is Open".format(dvdLocation), childCount)
		else:
			printColor("{} is Unknown state".format(dvdLocation), childCount)
	if isTrayHaveDVD(dvdLocation):
		printColor("{} is Full".format(dvdLocation), childCount)

def getDVDName(dvdLocation):
	# This gets the dvd name from the Volume name on the given location
	if not isTrayHaveDVD(dvdLocation):
		return ""
	else:
		cmd = ["setcd", "-i", "/dev/{}".format(dvdLocation)]
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		volumeName = ""
		for line in iter(p.stdout.readline, b''):
			if 'Volume name:' in str(line.rstrip()):
				volumeName = str(line.rstrip()).split('Volume name:')[1].replace(' ','').replace("'",'')
		return volumeName

def refreshTrayTimeTimerHelper(dvdLocation, childCount):
	# This is used to assist in the timer callback function
	# it has a bit of logic so that it doesn't just break things
	waitUntilReady(dvdLocation)
	if isTrayEmpty(dvdLocation):
		printColor('timer {} found an empty tray'.format(dvdLocation), childCount)
		openTray(dvdLocation)
	elif isTrayHaveDVD(dvdLocation):
		printColor('timer {} found a dvd in tray'.format(dvdLocation), childCount)
		return
	elif isTrayOpen(dvdLocation):
		refreshTrayTime(dvdLocation, childCount)

def setRefreshTrayTimer(dvdLocation, childCount):
	# This is used as a way to start new timer threads
	t1 = threading.Timer(refreshTrayTimerTime, refreshTrayTimeTimerHelper, [dvdLocation, childCount])
	t1.start()
	return t1

def getMakeMKVDiscNumber(dvdLocation):
	# This is used as a way to translate the sr# to makemkv disc:#
	# Returns a -1 if dvdLocation not found else returns the makemkv disc #
	
	# TODO in the future this should become a result from a singleton object
	cmd = ["makemkvcon", "-r", "--cache=1", "info", "disc:9999"]
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output = []
	for line in iter(p.stdout.readline, b''):
		output.append(line.rstrip())
	
	foundNumber = -1
	for line in output:
		if '/dev/sr' in str(line):
			if dvdLocation in str(str(line)[2:-2].split(',')[-1].replace("'",'')):
				foundNumber = str(str(line)[2:-2].split(',')[0].split(':')[1])
	return int(foundNumber)

def ripperHelper(dvdLocation, ripperFolder, childCount):
	# This is used as a way to simplify the ripperLogic function
	if os.path.isdir(ripperFolder):
		printColor("ERROR: ripperHelper: {} rip location already exists".format(dvdLocation), childCount)
		return
	
	os.mkdir(ripperFolder)
	driveNumber = getMakeMKVDiscNumber(dvdLocation)
	if driveNumber == -1:
		printColor("ERROR: ripperHelper: {} could not find driveNumber".format(dvdLocation), childCount)
		return
	
	cmd = ["makemkvcon", "mkv", "disc:{}".format(driveNumber), "all", "{}".format(ripperFolder), "--minlength={}".format(minTime)]

	with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as p:
		for line in p.stdout:
			printColor(line.decode("utf-8"), childCount)
	p_status = p.wait()
	printColor('{} finished Ripping at {}'.format(dvdLocation, ripperFolder), childCount)

def ripperLogic(dvdLocation, childCount):
	# This is used to attempt to rip a dvd from a disc tray
	dvdName = getDVDName(dvdLocation)
	ripperFolder = backupLocation+dvdName
	if dvdName == "":
		printColor("ERROR: ripperLogic: {} could not find dvdName".format(dvdLocation), childCount)
		return
	printColor("{} starting rip at {}".format(dvdLocation, ripperFolder), childCount)
	
	ripperHelper(dvdLocation, ripperFolder, childCount)
	openTray(dvdLocation)

def threadedRipperMain(dvdLocation, startTimeDelay, childCount):
	# This is the main logic of each dvd tray thread used for ripping
	time.sleep(startTimeDelay)
	t1 = setRefreshTrayTimer(dvdLocation, childCount)
	
	while True:
		time.sleep(1)
		if t1.is_alive() is False:
			t1 = setRefreshTrayTimer(dvdLocation, childCount)
		if isTrayHaveDVD(dvdLocation):
			t1.cancel()
			printColor('found DVD in {}'.format(dvdLocation),childCount)
			ripperLogic(dvdLocation, childCount)
			
			t1 = setRefreshTrayTimer(dvdLocation, childCount)
		if isTrayEmpty(dvdLocation):
			openTray(dvdLocation)

def getDVDList():
	return os.popen("ls /dev/ | grep sr").read().split('\n')[0:-1]


def main():
	# This is the main logic starter to start the program
	dvdList = getDVDList()
	
	runningProcesses = []
	delayTime = 0
	childNumber = 0
	for dvd in dvdList:
		# start with the tray open
		openTray(dvd)
		# prep the multiprocessing 
		runningProcesses.append( Process(target=threadedRipperMain, args=(dvd, delayTime, childNumber)) )
		delayTime = delayTime + 10
		childNumber = childNumber + 1
	
	for i in runningProcesses:
		# start the multi procossing
		i.start()
	
	for i in runningProcesses:
		# wait for the multi processing to end
		i.join()

if __name__ == "__main__":
	main()

