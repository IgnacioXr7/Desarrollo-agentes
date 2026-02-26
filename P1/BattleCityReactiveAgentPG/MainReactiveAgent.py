import sys
sys.path.insert(0,"./LGym")
sys.path.insert(0,"./Agent")
sys.path.insert(0,"./Reactive")
from LGym.LGymClient import agentLoop
from Agent.BaseAgent import BaseAgent
from Reactive.ReactiveAgent import ReactiveAgent


agent = ReactiveAgent("1","Isma")
agentLoop(agent,True)

 