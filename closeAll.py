import dvdManagerThreaded


def main():
        # This is the main logic starter to start the program
        dvdList = dvdManagerThreaded.getDVDList()

        for dvd in dvdList:
                # start with the tray closed
                dvdManagerThreaded.closeTray(dvd)
                
if __name__ == "__main__":
        main()





