import os
import time

backupLocation = "/hdd/"

dvdList = os.popen("ls /dev/ | grep sr").read().split('\n')[0:-1]
finsihedDvdLabels = []
knownUsedDvdDrives = []

while True:
	for dvd in dvdList:
		if dvd in knownUsedDvdDrives:
			os.system("eject /dev/{}".format(dvd))
			knownUsedDvdDrives.remove(dvd)
			time.sleep(10)

	time.sleep(1)

	for dvd in dvdList:
		if dvd not in knownUsedDvdDrives:
			time.sleep(10)
			os.system("eject -t /dev/{}".format(dvd))
			print("sleeping to get a good read up to 60 seconds")
			#for i in range(60):
			#time.sleep(1)
			commandText = "udevadm info -n {} -q property | sed -n 's/^ID_FS_LABEL=//p'".format(dvd)
			command = os.popen(commandText).read()
			hasDVD =(command!="")
			for i in range(60):
				if hasDVD:
					break
				time.sleep(1)
				command = os.popen(commandText).read()
				hasDVD = (command!="")

			print("{}: {}".format(command, hasDVD))
			#print(commandText)
			#print(str(type(command)))
			if hasDVD and command not in finsihedDvdLabels:
				finsihedDvdLabels.append(command)
				knownUsedDvdDrives.append(dvd)
				print("{} has found a dvd".format(dvd))
			else:
				if hasDVD:
					print("found dvd that was already done: {}".format(command))
				else:
					print("{} has no dvd".format(dvd))
				os.system("eject /dev/{}".format(dvd))
			#os.system("eject -t /dev/{}".format(dvd))
	time.sleep(10)
