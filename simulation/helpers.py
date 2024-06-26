import sys
import csv
import configparser
import ast
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import math
from simulation.mapMaker import Distance

#create agent

#NT: Create random coordinates for each agent
def create_coordinates(agents, maxDistance,):
    for agent in agents:
        agent.coordinates=np.random.uniform(0,maxDistance,2).tolist()

#create random coordinates in [x,y] shape, of trafficImage
def create_coordinates_nodes(agents, graph, tsp):
    #print(graph)
    for agent in agents:
        begin, dest=np.random.choice(graph.nodes, size=2, replace=False)
        #print(agent,": ",begin)

        agent.coordinates = graph.nodes[begin]['pos']
        #print(agent,": ",graph.nodes[begin]['pos'])
        agent.prev_dest = begin
        agent.destination = tsp(graph, nodes=[dest,begin], cycle=False)[1:] #set

        streetSlope=[ graph.nodes[agent.destination[0]]['pos'][0]- graph.nodes[begin]['pos'][0],  graph.nodes[agent.destination[0]]['pos'][1] - graph.nodes[begin]['pos'][1]  ]

        agent.vector=streetSlope/np.linalg.norm(streetSlope)
        #print(agent.vector)


#create base stations based on k-means clustering
def createBaseStations(numBaseStations, graph, reps):
    #print("\nCreateBaseStations")
    #print(len(graph.nodes))

    attempts=0
    while True:
        bsus = createBaseStationsRandomizer(numBaseStations,graph,reps)
        #print("\n\nBSUS:")
        classSize=[]
        for bs in bsus:
            #print(bs)
            #print(len(bs[2]))
            classSize.append(len(bs[2]))

        #print("classSize: ",classSize)
        #print("Minimum Cutoff:\t",((len(graph.nodes)/(numBaseStations))*2/3))
        if min(classSize)<((len(graph.nodes)/(numBaseStations))*2/3):
            attempts=attempts+1
            print("BAD BSU PLACEMENT:\t",attempts)
        else:
            return bsus

    #sys.exit("TESTING BEGONE")
    return bsus

def createBaseStationsRandomizer(numBaseStations, graph, reps):
    #print("\nCreateBaseStations")
    #print(len(graph.nodes))
    if numBaseStations>(len(graph.nodes)/2):
        sys.exit("Too Many BSUS, EXITING")

    #print(graph)
    bsus=[]
    nodesUsed=[]
    #initial starting points
    for bs in range(0,numBaseStations):
        loop=True
        while(loop):
            #print("\n\n",bsus)
            begin, dest=np.random.choice(graph.nodes, size=2, replace=False)
            #print(begin)
            #print(graph.nodes)
            #print(graph.nodes[node])
            #print(graph.nodes[begin]['pos'])
            coordinate=graph.nodes[begin]['pos']

            #print("TESTING:")
            #for b in bsus:
                #print(b[1])

            if begin not in nodesUsed:
                nodesUsed.append(begin)
                #[ID, current Coordinate, clustered nodes, average clustered Node]
                bsus.append([bs,coordinate, [], [], [0,1]])
                loop=False
    #bsus  = [[id,coordinate]]
    #print("Creation Done: ", bsus)

    #k means time
    for i in range(0,reps):
        #print("\nRep: ",i)
        #print(bsus)
        #0. get rid of useless data]
        for bs in bsus:
            bs[2]=[]
            bs[3]=[]
        #1. Classify all nodes
        for n in graph.nodes:
            #print("\n",n)
            closest = 10000000
            closestBS = -1
            for bs in bsus:
                #print(bs)
                #print(bs[1])
                coord= graph.nodes[n]['pos']
                diff = Distance(coord,bs[1])
                #print("DIFF: ",diff)
                if diff<closest:
                    closest=diff
                    closestBS = bs[0]
                    #print(closestBS)
            bsus[closestBS][2].append(n)
            bsus[closestBS][3].append(coord)

        #2. Get mean of all nodes
        for bs in bsus:
            average = [sum(x)/len(x) for x in zip(*bs[3])]
            bs[4] =average

        #print("Mean Done:")
        #for bs in bsus:
            #print(bs)

        #3. Assign mean of each cluster to closest node
        for bs in bsus:
            closest = 10000000
            closestNode = -1
            for n in bs[2]:
                coord= graph.nodes[n]['pos']
                diff = Distance(coord,bs[4])
                if diff<closest:
                    closest=diff
                    closestNode = n
            bs[1]=graph.nodes[closestNode]['pos']
            #print(closest)
        #for bs in bsus:
            #print(bs)
        #4. Remove classification

    #sys.exit("TESTING BEGONE")
    return bsus



def update_progress(progress, time):

    bar_length = 50
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
    if progress < 0:
        progress = 0
    if progress >= 1:
        progress = 1
        status = "| Simulation completed...\r\n"
    block = int(round(bar_length*progress))
    text = "\rPercent:  [{0}] {1}% | Number:  {2} {3}".\
        format( "#"*block + "-"*(bar_length-block), np.round((progress*100),1), time, status)
    sys.stdout.write(text)
    sys.stdout.flush()


def create_distance_matrix(no_of_agents, distance):

    m = [[distance] * no_of_agents for i in range(no_of_agents)]
    for i in range(no_of_agents):
        m[i][i] = 0
    return m


def create_random_graph_distances(no_of_agents):

    n = no_of_agents  #number nodes
    m = n  #number edges

    G = nx.gnm_random_graph(n, m)

    while not nx.is_connected(G):
        G = nx.gnm_random_graph(n, m)

    distances = (nx.floyd_warshall_numpy(G)).tolist()

    print("Closeness centrality per agent:  " + str(nx.closeness_centrality(G)))

    # print the random graph
    nx.draw(G, with_labels=True)
    # plt.savefig('agent_graph.png')

    return distances


def common_elements(a, b):

    a_set = set(a)
    b_set = set(b)

    if len(a_set.intersection(b_set)) > 0:
        return list((a_set.intersection(b_set)))
    else:
        return []


def clamp(val, minimum=0, maximum=255):
    if val < minimum:
        return minimum
    if val > maximum:
        return maximum
    return val


def load_file(filename):

    try:
        config = configparser.ConfigParser()
        config.read(filename)
        data = []
        simulation_config_parameters = config['PARAMETERS']

        #Check if all simulation parameters provided
        if not all(key in simulation_config_parameters.keys() for key in ['no_of_transactions','lambda','no_of_agents',\
                                                                      'alpha','latency','distance','tip_selection_algo',\
                                                                      'agent_choice','printing']):

            print("Parameter error! Please provide 'no_of_transactions','lambda','no_of_agents','alpha','latency',"
            "'distance','tip_selection_algo','agent_choice','printing'!")
            sys.exit(1)

        #Load simulation parameters
        _no_of_transactions = int(simulation_config_parameters['no_of_transactions'])
        _lambda = float(simulation_config_parameters['lambda'])
        _no_of_agents = int(simulation_config_parameters['no_of_agents'])
        _alpha = float(simulation_config_parameters['alpha'])
        _latency = int(simulation_config_parameters['latency'])

        if (type(ast.literal_eval(simulation_config_parameters['distance'])) is list):
            _distance = ast.literal_eval(simulation_config_parameters['distance'])
        else:
            _distance = create_distance_matrix(_no_of_agents,float(simulation_config_parameters['distance']))

        _tip_selection_algo = simulation_config_parameters['tip_selection_algo']

        if (simulation_config_parameters['agent_choice'] == 'None'):
            _agent_choice = list(np.ones(_no_of_agents) / _no_of_agents)
        else:
            _agent_choice = ast.literal_eval(simulation_config_parameters['agent_choice'])

        _printing = config.getboolean('PARAMETERS','printing')

        data.append((_no_of_transactions, _lambda, _no_of_agents, \
        _alpha, _latency, _distance, _tip_selection_algo, _agent_choice, _printing))

        #Load change parameters
        for key in config:
            if(key != 'PARAMETERS' and key != 'DEFAULT'):

                event_change_parameters = config[key]

                if 'step' not in event_change_parameters:
                    print("Please provide a 'step' for the parameter change!")
                    sys.exit(1)
                step = int(event_change_parameters['step'])

                if 'distance' not in event_change_parameters:
                    _distance = False
                elif (type(ast.literal_eval(event_change_parameters['distance'])) is list):
                    _distance = ast.literal_eval(event_change_parameters['distance'])
                else:
                    _distance = create_distance_matrix(_no_of_agents,float(event_change_parameters['distance']))

                if 'agent_choice' not in event_change_parameters:
                    _agent_choice = False
                elif (event_change_parameters['agent_choice'] == 'None'):
                    _agent_choice = list(np.ones(_no_of_agents) / _no_of_agents)
                else:
                    _agent_choice = ast.literal_eval(event_change_parameters['agent_choice'])
                    if (round(sum(_agent_choice), 3) != 1.0):
                        print("Agent choice not summing to 1.0: {}".format(sum(_agent_choice)))
                        sys.exit(1)
                    if (len(_agent_choice) != _no_of_agents):
                        print("Agent choice not matching no_of_agents: {}".format(len(_agent_choice)))
                        sys.exit(1)

                data.append((step, _distance, _agent_choice))

    except Exception as e:
        print(e)

    return data


def routes_export(file_name, agents):
    with open(file_name, 'w', newline='') as file:
        writer = csv.writer(file, dialect='excel')
        for agent in agents:
            writer.writerow(agent.destination)





def routes_importer(simulation, file_name):
    with open(file_name, 'r') as file:
       reader = csv.reader(file,quoting = csv.QUOTE_NONNUMERIC, delimiter = ',')
       data_list = list(reader)
       #print(data_list)
       for index, readDestinations in enumerate(data_list):
           simulation.agents[index].destination=readDestinations
       #sys.exit("END ROUTES_IMPORTER")


def confirmationLayer_importer(simulation, file_name):
    with open(file_name, 'r') as file:
       reader = csv.DictReader(file,quoting = csv.QUOTE_NONNUMERIC, delimiter = ',')
       #data_list = list(reader)

       print(simulation.blockTime, " ",simulation.no_of_agents," ", simulation.importMap, " ",simulation.DLTMode," ", simulation.references, " ",simulation.consensus, " ", simulation.group)
      # print("\n\n")
       for row in reader:
           blockTime = row['blockTime']
           numAgents = row['numAgents']
           map = row['map']
           dlt = row['dlt']
           refs = row['refs']
           consensus = row['consensus']
           group = row['group']
           #if consensus==simulation.consensus:
               #print(blockTime, " ",int(numAgents)," ", map, " ",dlt," ", int(refs), " ",consensus, " ",int(group))
               #print((numAgents))
               #print(int(numAgents)==int(simulation.no_of_agents))
               #if int(simulation.no_of_agents) == int(numAgents):
                   #print(blockTime, " ",int(numAgents)," ", map, " ",dlt," ", int(refs), " ",consensus, " ",int(group))
                   #print(simulation.blockTime, " ",simulation.no_of_agents," ", simulation.importMap[:-4], " ",simulation.DLTMode," ", simulation.references, " ",simulation.consensus, " ",simulation.group)



           if (int(simulation.blockTime) == int(blockTime) and int(simulation.no_of_agents) == int(numAgents) and simulation.importMap[:-4] == map):
               if (simulation.DLTMode == dlt and int(simulation.references) == int(refs)):

                   if(int(simulation.group)==int(group) and simulation.consensus==consensus):
                       #print("Found ConfirmationNumber: ",row['confirmationNumber'],"\t",row)
                       return int(row['confirmationNumber'])
            #sys.exit("MATCH DEBUGGING DONE")

           #print(row['blockTime'], " ~ ",row['numAgents'])
       if simulation.DLTMode =="dht" or simulation.DLTMode=="hashgraph":
           print("DHT/Hashgraph no Confirmation Needed")
           return int(3)
       #sys.exit("No Confirmation Layer Found, RECOMPUTE")
       ##linear check for 2 References

    with open(file_name, 'r') as file:
       reader = csv.DictReader(file,quoting = csv.QUOTE_NONNUMERIC, delimiter = ',')

       if simulation.DLTMode=="linear": #check for 1
           print("Recheck for ref=2 because Linear")
           for row in reader:
               blockTime = row['blockTime']
               numAgents = row['numAgents']
               map = row['map']
               dlt = row['dlt']
               refs = row['refs']
               consensus = row['consensus']
               group = row['group']
               # print(consensus)
               # if consensus==simulation.consensus:
               #     print(blockTime, " ",int(numAgents)," ", map, " ",dlt," ", int(refs), " ",consensus, " ",int(group))
               #     print((numAgents))
               #     print(int(numAgents)==int(simulation.no_of_agents))
               #     if int(simulation.no_of_agents) == int(numAgents):
               #         print(blockTime, " ",int(numAgents)," ", map, " ",dlt," ", int(refs), " ",consensus, " ",int(group))
               #         print(simulation.blockTime, " ",simulation.no_of_agents," ", simulation.importMap[:-4], " ",simulation.DLTMode," ", simulation.references, " ",simulation.consensus, " ",simulation.group)



               if (int(simulation.blockTime) == int(blockTime) and int(simulation.no_of_agents) == int(numAgents) and simulation.importMap[:-4] == map):

                   if (simulation.DLTMode == dlt and int(2) == int(refs)):

                       if(int(simulation.group)==int(group) and simulation.consensus==consensus):
                          # print("Found ConfirmationNumber: ",row['confirmationNumber'])
                           return int(row['confirmationNumber'])


       print("NO CONFIRMATION LAYER FOUND, USE THESE RESULTS FOR COMPUTING CONFIRMATION LAYER")
       #sys.exit("NO CONF, ERROR")
       return int(3)

def csv_export(self, file_name):

    with open(file_name, 'w', newline='') as file:
        writer = csv.writer(file, dialect='excel')
        #Write csv file header
        if self.DLTMode == "hashgraph":
            header=['ID', 'confirmedBlock', 'confirmationTime', 'chainNum', 'orderTime', 'confirmed_blocks', 'tips', 'arrival_time', 'agent',  'adoption_rate', 'block_transactions', 'transaction_creation_time']

        else:
            header=['ID', 'confirmedBlock', 'confirmationTime', 'chainNum', 'confirmed_blocks', 'tips', 'arrival_time', 'agent',  'adoption_rate', 'block_transactions', 'transaction_creation_time']
        #print(self.DG.nodes[0].id)
        #print(self.DG.nodes[0].seen)

        #add header for agentSeen
        for i in range(0,self.no_of_agents):
            header.append(str("agent_"+str(i+1)))

        #add headers for RSUseen
        for i in range(0,self.basestations):
            header.append(str("basestation_"+str(i+1)))


        # for transaction in self.DG.nodes:
        #     #print("seenList: ",transaction.seen)
        #     for agentId, agentSeen in enumerate(transaction.seen):
        #         header.append(str("agent_"+str(agentId+1)))
        #     break



        #print(header)
        writer.writerow(header) #add confirmation time +
        #Write genesis
        #writer.writerow([0,[],0, '', 0, 0])
        for block in self.DG.nodes:
            #Write all other transactions
            #if(block.creation_time != 0):
            #print("\nBlock:\t",block.id,"\t",block.creation_time)
            #print("creator:\t",block.creators)
            line = []
            line.append(block.id) #txid
            line.append(block.confirmed)
            line.append(block.confirmationTime)
            line.append(block.chainNum)
            if self.DLTMode == "hashgraph":
                line.append(block.orderTime)
            line.append(block.confirmedBlocks)
            line.append(list(self.DG.successors(block))) #tips
            line.append(block.creation_time) #arrival_time
            line.append(block.creators) ##int(transaction.creators[0].id)+1) #agent


            #line.append(0) ##line.append(transaction.tip_selection_time
            #line.append(0) ## line.append(transaction.weight_update_time)
            line.append(len(list(nx.descendants(self.DG, block)))/(block.id+0.001)) #adoption_rate
            block.blockTransactions = sorted(block.blockTransactions,key=lambda x: x.id) #sort blockTransactions before printing
            #print("\n\n",block.id, ".blockTransactions: ",block.blockTransactions)
            line.append(block.blockTransactions)

            txtimes = []
            for tx in block.blockTransactions:
                txtimes.append(math.ceil(tx.arrival_time))

            #arrival time of all txs
            line.append(txtimes)

            for agentSeen in block.seen:
                line.append(agentSeen)
                #print("agentSeen:\t",agentSeen)
            writer.writerow(line)


def volume_export(self,file_name):
    with open(file_name, 'w', newline='') as file:
        writer = csv.writer(file, dialect='excel')
        #Write csv file header
        headers = ['time','numTxs','numBlocks','maxNumTxs','maxNumBlocks','blockTxs']
        #print(self.DG.nodes[0].id)
        #print(self.DG.nodes[0].seen)

        #print(header)
        writer.writerow(headers) #add confirmation time +
        #Write genesis
        #writer.writerow([0,[],0, '', 0, 0])
        for line in self.agents[0].storageData:
            writer.writerow(line)


def p2p_export(self,file_name1,file_name2):
    ##Don't need interaction for now
    #with open(file_name1, 'w', newline='') as file:
    #    writer = csv.writer(file, dialect='excel')
        #Write csv file header
    #    headers = ['time', 'uVisTx', 'dVisTx', 'tVisTx', 'uSubTx', 'dSubTx', 'tSubTx',  'uConTx', 'dConTx', 'tConTx', 'uVisBlock', 'dVisBlock', 'tVisBlock', 'uLinkBlock', 'dLinkBlock', 'tLinkBlock','uTxs', 'dTxs', 'tTxs', 'uBlocks', 'dBlocks', 'tBlocks']
        #print(self.DG.nodes[0].id)
        #print(self.DG.nodes[0].seen)

        #print(header)
    #    writer.writerow(headers) #add confirmation time +
        #Write genesis
        #writer.writerow([0,[],0, '', 0, 0])
    #    for agent in self.agents:
    #        for line in agent.p2pData:
    #            writer.writerow(line)
    with open(file_name2, 'w', newline='') as file:
        writer = csv.writer(file, dialect='excel')
        #Write csv file header
        headers = ['time','selfagentid', 'agentid','p2pTime']
        #print(self.DG.nodes[0].id)
        #print(self.DG.nodes[0].seen)

        #print(header)
        writer.writerow(headers) #add confirmation time +
        #Write genesis
        #writer.writerow([0,[],0, '', 0, 0])
        for agent in self.agents:
            for line in agent.p2pHistory:
                writer.writerow(line)


def tx_export(self,file_name):
    with open(file_name, 'w', newline='') as file:
        writer = csv.writer(file, dialect='excel')
        #Write csv file header
        headers = ['type','time', 'numTxs', 'txid', 'txAgent', 'arrival_time', 'age', 'recipientAgent', 'new']
        #print(self.DG.nodes[0].id)
        #print(self.DG.nodes[0].seen)

        #print(header)
        writer.writerow(headers) #add confirmation time +
        #Write genesis
        #writer.writerow([0,[],0, '', 0, 0])
        for agent in self.agents:
            for line in agent.txTrade:
                writer.writerow(line)
