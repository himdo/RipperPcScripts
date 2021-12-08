import subprocess, os

file_location = "/hdd"
outputLocation = "/complete/"

for root, dirs, files in os.walk(file_location, topdown=False):
   for name in dirs:
      if name == outputLocation.split("/")[1]:
         continue
      #print(os.path.join(root, name))
      for root_1, dirs_1, files_1 in os.walk(os.path.join(root, name), topdown=False):
         for name_files in files_1:
            print(os.path.join(root_1, name_files))
            fullDir = file_location + outputLocation + name
            if not os.path.exists(fullDir):
               os.makedirs(fullDir)
            fullFileLocation = fullDir + "/" + name_files
            if os.path.exists(fullFileLocation):
               continue
            cmd = ["ffmpeg", "-i", "{}".format(os.path.join(root_1, name_files)), "-c:v", "libx265", "-vcodec", "libx265", "-crf", "24", "{}".format(fullFileLocation)]
            print(cmd)

            with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as p:
               for line in p.stdout:
                  print(line.decode("utf-8"))
