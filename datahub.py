import urllib
import urllib2
import json
import re
import math

from urllib2 import HTTPError, URLError 

# todos: 
# - check on runtime whether the URLs given are alive	# ok ... but now it's REALLY slow
# - check on runtime whether format is RDF or OWL		# for many dataset, the metadata is incomplete, e.g., dbpedia-ko, hence later

# meta data categories:
# via tags:
# "corpus" => llod:corpus
# "lexicon", "wordnet" => llod:corpus
# (none of these) => llod:language_description

baseURL = "http://datahub.io/api/3/action/"
blacklist = [
'masc', 																				# rdf export... not linked data
'apertium', 																			# not rdf
'wiktionary-en', 																		# not rdf
'wordnet', 																				# not rdf
'saldo', 																				# not rdf
'xwn', 																					# not rdf
'talkbank', 																			# not rdf
'french-timebank', 																		# not rdf
'jmdict', 																				# not rdf
'multext-east', 																		# not rdf
'wikiword_thesaurus', 																	# not rdf
'eu-dgt-tm', 																			# not rdf
'multilingualeulaw', 																	# not rdf
'wiktionary', 																			# not rdf
'omegawiki', 																			# not rdf
'framenet', 																			# not rdf
'o-anc', 																				# not rdf
'conceptnet', 																			# not rdf
'phoible', 																				# not rdf
'opus', 																				# not rdf
# 'sanskrit-english-lexicon', 															# down	# CC: checked at runtime
# 'pali-english-lexicon', 																# down	# CC: checked at runtime
'dbpedia-spotlight', 																	# tool not data!
'ss', 																					# spam
'cgsddforja', 																			# spam
'sqxfetge', 																			# spam
'fafqwfaf', 																			# spam
'sqxfetgea', 																			# spam
'printed-book-auction-catalogues' 														# spam ?
'analisi-del-blog-http-www-beppegrillo-it', 											# spam
'cosmetic-surgeon-wearing-nursing-scrubs-nursing-uniforms-expert-scrubs-for-safety' 	# spam
]

def ckanListDatasetsInGroup(group):
  url = baseURL + "group_show?id=" + group
  return json.loads(urllib2.urlopen(url).read())

def ckanDataset(dataset):
  url = baseURL + "package_show?id=" + dataset
  return json.loads(urllib2.urlopen(url).read())

nodes = {}

datasetJSON = ckanListDatasetsInGroup("linguistics")
datasets = [ds["name"] for ds in datasetJSON["result"]["packages"]]
datasets = set(datasets) - set(blacklist)
for dataset in datasets:
  nodes[dataset] = {}
  nodes[dataset]["edgecount"] = 0

for dataset in datasets:
  print("Dataset:" + dataset)
  dsJSON = ckanDataset(dataset)
  nodes[dataset]["url"] = baseURL + "package_show?id=" + dataset
  nodes[dataset]["name"] = dsJSON["result"]["title"]
  nodes[dataset]["links"] = {}

  nodes[dataset]["aliveurls"] = 0
  nodes[dataset]["deadurls"] = 0
  nodes[dataset]["formats"] = 0
  nodes[dataset]["rdf_owl"] = 0
   
  # check whether URLs given are alive
  try: urllib2.urlopen(urllib2.Request(dsJSON["result"]["url"]))
  except HTTPError as e:
    print "HTTPError "+str(e.code)+" while trying to access "+dsJSON["result"]["url"]
    nodes[dataset]["deadurls"] += 1
  except ValueError:
    try: urllib2.urlopen(urllib2.Request("http://"+dsJSON["result"]["url"]))
    except HTTPError as e1:
      print "HTTPError "+str(e1.code)+" while trying to access "+dsJSON["result"]["url"]
      nodes[dataset]["deadurls"] += 1
    except URLError as e1:
	  print "URLError "+e1.reason+" while trying to access "+dsJSON["result"]["url"]
	  nodes[dataset]["deadurls"] += 1
    else: nodes[dataset]["aliveurls"] += 1
  except HTTPError as e:
    print "HTTPError "+str(e.code)+" while trying to access "+dsJSON["result"]["url"]
    nodes[dataset]["deadurls"] += 1
  except URLError as e:
    print "URLError "+str(e.args)+" while trying to access "+dsJSON["result"]["url"]
    nodes[dataset]["deadurls"] += 1
  else: nodes[dataset]["aliveurls"] += 1
  
  for res in dsJSON["result"]["resources"]:
    try: urllib2.urlopen(urllib2.Request(res["url"]))
    except HTTPError as e:
      print "HTTPError "+str(e.code)+" while trying to access "+res["url"]
      nodes[dataset]["deadurls"] += 1
    except ValueError:
      try: urllib2.urlopen(urllib2.Request("http://"+res["url"]))
      except HTTPError as e1:
        print "HTTPError "+str(e1.code)+" while trying to access "+res["url"]
        nodes[dataset]["deadurls"] += 1
      except URLError as e1:
        print "URLError "+str(e1.args)+" while trying to access "+res["url"]
        nodes[dataset]["deadurls"] += 1
      else: nodes[dataset]["aliveurls"] += 1
    except HTTPError as e:
      print "HTTPError "+str(e.code) +" while trying to access "+res["url"]
      nodes[dataset]["deadurls"] += 1
    except URLError as e:
      print "URLError "+str(e.args) +" while trying to access "+res["url"]
      nodes[dataset]["deadurls"] += 1
    else: nodes[dataset]["aliveurls"] += 1
  print("alive: " +str(nodes[dataset]["aliveurls"])+"/"+str(nodes[dataset]["aliveurls"]+nodes[dataset]["deadurls"]))
	 
  # count links
  for kv in dsJSON["result"]["extras"]:
    if(re.match("links:.*",kv["key"])):
      target = kv["key"][6:]
      s = float(kv["value"][0:(len(kv["value"]))])
      print(dataset + " => " + target + ": weight " + kv["value"])
      if target in nodes.keys():
        nodes[dataset]["links"][target] = s
        nodes[dataset]["edgecount"] += 1
        nodes[target]["edgecount"] += 1
      else:
        print("External edge:" + target)
    if(kv["key"] == "triples"):
      nodes[dataset]["triples"] = kv["value"][1:(len(kv["value"])-1)]

  # for debugging only
  with open("llod-cloud.json","w") as outfile:
    json.dump(nodes,outfile,indent=4)
	  
# we do NOT exclude unlinked data sets (at the moment)
#for v in nodes.keys():
#  if(nodes[v]["edgecount"] == 0):
#    del nodes[v]

# we exclude everything that's totally down
for v in nodes.keys():
  if(nodes[v]["aliveurls"] == 0):
    del nodes[v]

with open("llod-cloud.json","w") as outfile:
  json.dump(nodes,outfile,indent=4)
