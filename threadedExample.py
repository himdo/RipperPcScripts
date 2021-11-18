from multiprocessing import Process
import time, random
def func1():
	print ('func1: starting')
	for i in range(10000000): pass
	print ('func1: finishing')

def func2(test):
	print(test)
	print ('func2: starting')
	time.sleep(random.randrange(4)) #for i in range(10000000): pass
	print ('func2: finishing')

list1 = []
workingList = []
maxListSize = 18

if __name__ == '__main__':
	for i in range(10):
		p1 = Process(target=func1)
		list1.append(p1)
	for i in range(10):
		p2 = Process(target=func2, args=("test",))
		list1.append(p2)
	startTime = time.time()

	while len(list1):
		while len(workingList) < maxListSize:
			if len(workingList) < maxListSize:
				if len(list1) > 0:
					item = list1[-1]
					list1 = list1[0:-1]
					item.start()
					workingList.append(item)
			if len(list1) == 0:
				break
		time.sleep(1)
		recentFinishedList = []
		for i in range(len(workingList)):
			if workingList[i].exitcode is not None:
				recentFinishedList.append(workingList[i])
		for i in range(len(recentFinishedList)):
			workingList.remove(recentFinishedList[i])

	print("time took: {}".format(time.time()-startTime))

