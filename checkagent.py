#coding=gbk
from multiprocessing import Queue
import requests
from concurrent.futures import ThreadPoolExecutor
import time

agent_queue=Queue()

with open('agent') as f:
    my_headers = f.readlines()
for i in my_headers:
    agent_queue.put(i.replace('\n', ''))
    #print()

print(agent_queue.qsize())
def agents():
    while not agent_queue.empty():
        agent=agent_queue.get()
        try:
            response = requests.get('https://www.kuaidaili.com/free/inha/3/',headers={"User-Agent":agent},timeout=5)
            print('\033[1;34m'+'%d  %s'%(agent_queue.qsize(),agent)+'\033[0m')
        except:
            print(agent)

pool=ThreadPoolExecutor(20)
if __name__ == '__main__':
    for i in range(20):
        pool.submit(agents)
