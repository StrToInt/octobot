import sys
import os

def main():
    #filepath = sys.argv[1]
    #filepath2 = sys.argv[1]
    filepath = 'temps.txt'
    filepath2 = 'information.txt'

    temps = []

    with open(filepath,'r') as fp:
        line = fp.readline()
        while line:
            t = line.split('|')
            if len(t) == 2:
                try:
                    t[1] = t[0]+str(int(t[1])/1000)+'°C'
                except:
                    t[1] = t[0]+'неверное число'
                finally:
                    temps.append(t[1])
            line = fp.readline()

    print(temps)

    with open(filepath2,'w') as fp2:
        for t in temps:
            fp2.write(t+"\n")



if __name__ == '__main__':
    main()