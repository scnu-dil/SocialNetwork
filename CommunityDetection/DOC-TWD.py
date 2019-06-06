#coding=utf-8
import networkx as nx
import string
class DOCTW:
	def __init__(self,a=0,b=-0.01,e=0.5):
		# two threholds for fitness function
		self.a = a
		self.b = b
		self.e = e

	def execute(self,G):
		RC = list()  # the result of clustering
		CC = list()  # all of cluster core
		# classify nodes
		bone_nodes = set()  # core and bone nodes
		trivial_nodes = set()  # trivial nodes
		self._Weight_all(G)
		for v in G.nodes:
			score = self._LIV(G,v)
			if score > 0:
				bone_nodes.add(v)
			else:
				trivial_nodes.add(v)
		bone_G = nx.Graph(G.subgraph(bone_nodes))
		trivial_G = nx.Graph(G.subgraph(trivial_nodes))

		# cluster core
		for v in G.nodes:
			if G.nodes[v]['score'] == 1:
				CC += self._ClusterCore(G,v)
		print("CC size:%d"%len(CC))
		for cc in CC:
			RC.append({'positive':set(cc.nodes),'boundary':set()})
		# preliminary clustering
		for v in bone_nodes:
			cc_location = 0
			cc_count = 0
			low_b_count = 0
			highest_u = -10000
			highest_rc = None
			for rc,cc in zip(RC,CC):
				if len(set(G.adj[v].keys()) & rc['positive']):#set(cc.nodes)):
					u = self._u(G,G.subgraph(rc['positive']),v)
					cc_count += 1
					if u >= self.a:
						rc['positive'].add(v)
					else:
						if u >= self.b:
							rc['boundary'].add(v)
						else:
							low_b_count += 1
							if u > highest_u:
								highest_rc = cc_location
				cc_location += 1
			if cc_count == low_b_count and highest_rc:
				RC[highest_rc]['boundary'].add(v)
		
		# merger trivial nodes
		for v in trivial_nodes:
			cc_location = 0  # record the no of current cluster core
			cc_count = 0  # the number of cluster core
			low_b_count = 0  # judge all u(v,C) < b
			highest_u = -10000  # initial number may be some problem
			highest_rc = None
			for rc,cc in zip(RC,CC):
				#  judge node v adjacent to which cluster core
				if len(set(G.adj[v].keys()) & rc['positive']):#set(cc.nodes)):
					u = self._u(G,G.subgraph(rc['positive']),v)
					cc_count += 1
					if u >= self.a:
						rc['positive'].add(v)
					else:
						if u >= self.b:
							rc['boundary'].add(v)
						else:
							low_b_count += 1
							if u > highest_u:
								highest_rc = cc_location
				cc_location += 1
			if cc_count == low_b_count and highest_rc:
				RC[highest_rc]['boundary'].add(v)
		for rc in RC:
			print("*"*10)
			print(rc['positive'])
			print(rc['boundary'])
			print("*"*15)
		# merger clusters
		community = list()
		merge_mark = list()
		for i in range(len(RC)):
			for j in range(i+1,len(RC)):
				#print(i,j)
				if self._DegPOP(RC[i]['positive'],RC[j]['positive']) >= self.e:
						merge_mark += [i,j]
						print(i,j)
						merger = RC[i]['positive'] | RC[i]['boundary'] | RC[j]['positive'] | RC[j]['boundary']
						community.append(merger)
		for i in list(set([i for i in range(len(RC))]) - set(merge_mark)):
			community.append(RC[i]['positive'] | RC[i]['boundary'])
		print(community)
		return community

	def _ClusterCore(self,G,v):
		sub_nodes = set()
		sub_nodes.add(v)
		for n in G[v].keys():
			sub_nodes.add(n)
		sub_G = nx.Graph(G.subgraph(sub_nodes))
	
		sub_G.remove_node(v)
		clusters = list()  # all of maximal connected subgraphs
		drop_nodes = list()  # node in the subgraph which has only one node
		for c in nx.connected_components(sub_G):
			if len(c) > 1:
				clusters.append(nx.Graph(sub_G.subgraph(c)))
			else:
				drop_nodes.append(list(c)[0])
		#v_edges = [(v,u) for u in G[v] if u not in drop_nodes]
		final_clusters = list()
		for cluster in clusters:
			c_nodes = list(cluster.nodes)
			for u in c_nodes:
				cluster.add_node(v,role=G.nodes[v]['role'])  # todo:add someattributes
				cluster.add_edge(v,u,weight=G.edges[v,u]['weight'])
			final_clusters.append(cluster)
		return final_clusters

	def _u(self,G,C,v):
		Cv_nodes = list(C.nodes) + [v]  # may be some bugs !!!
		Cv = nx.Graph(G.subgraph(Cv_nodes))  # union C and v,may be some bugs
		score = self._fitness_func(G,Cv) - self._fitness_func(G,C)
		#print(v,score)
		return score
		
	def _fitness_func(self,G,C):
		Win = 0
		Wout = 0
		for (u, v, wt) in C.edges.data('weight'):
			Win +=  wt
		for v in C.nodes:
			out_nodes = set(G.adj[v].keys()) - set(C.adj[v].keys())
			#print(v,out_nodes)
			for u in list(out_nodes):
				Wout += G.edges[v,u]['weight']
		score = Win / (Win + Wout)
		return score

	def _Weight_all(self,G):
		for n, nbrs in G.adj.items():
			n_weight = 0
			for nbr, eattr in nbrs.items():
				n_weight += float(eattr['weight'])
			G.nodes[n]['weight'] = n_weight

	def _LIV(self,G,v):
		A = 0
		Adj_v = len(G[v].keys())
		for n,attr in dict(G[v]).items():
			#if v == "Stannis":
			#	print(n,G.nodes[n]['weight'],G.nodes[v]['weight'])
			if G.nodes[n]['weight'] <= G.nodes[v]['weight']:
				A += 1
		#if v == "Stannis":
		#	print(v,A,Adj_v)
		score = A / Adj_v
		if score == 1:
			role = "core"
		elif score == 0:
			role = "trivial"
		else:
			role = "bone"
		G.nodes[v]['role'] = role
		G.nodes[v]['score'] = score
		return score

	def _DegPOP(self,Ci,Cj):
		"""
		todo:计算DegPOP值
		"""
		score = len(Ci & Cj) / min(len(Ci),len(Cj))
		return score

	def _is_extended(self,Ci,Cj):
		if Ci.number_of_nodes > Cj.number_of_nodes:
			return True
		return False
			
if __name__ == "__main__":
	"""
	#定义图的节点和边 
	nodes=['0','1','2','3','4','5','6','a','b','c'] 
	edges=[('0','1',1),('0','5',1),('1','5',1),('1','6',1),('0','5',2),('1','2',3),('1','4',5),('2','1',7),('2','4',6),('a','b',0.5),('b','c',0.5),('c','a',0.5)] 
 	"""
	from py2neo import Graph
	from igraph import Graph as IGraph
	graph = Graph("http://localhost:7474",username="neo4j",password="password")
	query = '''
		MATCH (c1:Character)-[r:INTERACTS]->(c2:Character)
		RETURN c1.name, c2.name, r.weight AS weight
		'''
	"""
	#定义graph 
	G = nx.Graph() 
	#G.add_nodes_from(nodes) 
	G.add_weighted_edges_from(graph.run(query))
	#print(G.edges)
	#print(G['Brynden'])
	"""
	f = open("/home/jiaqi/something/relationship_count/merge_all.csv","r")
	i = 0
	j = 0
	al = list()
	for l in f.readlines():
        	i += 1
        	l = l.strip().split(",")
        	for a in l[:i-1]:
                	j += 1
                	if a != '0':
                        	#print(i,j,a)
                	        al.append((i,j,float(a)))
        	j = 0
	print(len(al))
	f.close()
	G = nx.Graph()
	G.add_weighted_edges_from(al)
	#print(G.edges)
	#print(G[1])
	doctw = DOCTW()
	
	comm = doctw.execute(G)
	num = 0
	temp = set()
	for i,c in enumerate(comm):
		temp = temp | set(c)
		for n in c:
			num += 1
			G.nodes[n]["community_doctw"] = i
	print(set(G.nodes) - temp)
	"""
	nodes = [{"name": G.nodes[n],"community_doctw":G.nodes[n]["community_doctw"]} for n in G.nodes]
	write_clusters_query = '''
		UNWIND {nodes} AS n
		MATCH (c:Character) WHERE c.name = n.name
		SET c.community = toInt(n.community)
		'''

	graph.run(write_clusters_query, nodes=nodes)
	
	G = nx.Graph()
	#G.add_nodes_from(nodes) 
	G.add_weighted_edges_from(graph.run(query))
	doctw._Weight_all(G)
	#print(G.nodes['Brynden'])
	for v in G.nodes:
		doctw._LIV(G,v)
		print(v,G.nodes[v]["role"])
	for v in G.nodes:
		score = doctw._LIV(G,v)
		if score == 1:
			print("core node:%s"%str(v))
			print([c.nodes for c in doctw._ClusterCore(G,v)])
			for c in doctw._ClusterCore(G,v): 
				print("-"*30)
				for v in c.nodes:
					print(v,c.nodes[v]['role'])
					#print(G.adj[v])
				print("-"*30)
	"""
