
# coding: utf-8

# # Python dependencies

# In[1]:


#Dependencies
import json
from hashlib import sha256
import time
import datetime

# # Creating a single block

# In[2]:


"""
This class is used to create a single block in the blockchain and is called by the below class, "Blockchain"
"""
#To make sure we are recording the transaction in the blockchain
class Block:
	def __init__(self, index, transaction, timestamp, prevHash):
		self.index = index
		self.transactions = transaction
		self.prevHash = prevHash
		self.timestamp = timestamp 
		self.nonce = 0
		
	def generate_hash(self):#Encrypt the transaction using the SHA256 method
		block_entry = json.dumps(self.__dict__ , sort_keys=True)
		return sha256(block_entry.encode()).hexdigest()
# # Creating the blockchain
# In[3]:
"""
This class is used to create the genesis block and subsequently conjoin blocks to make the blockchain network. It calls the "Block" class as a subroutine in order to synthesise 
a singular block or entry.
"""
class Blockchain:
	difficulty = 2 #hash must begin with 2 leading zeroes
	def __init__(self):
		self.unconfirmedTransactions = []# Transactions that have not yet been mined
		self.chain = []
		self.createGenesisBlock()
		
	def createGenesisBlock(self):
		genesisBlock = Block(0, [], time.time(), "0")#Call block routine to synthesise the first block, the genesis block
		genesisBlock.hash = genesisBlock.generate_hash()# Encrypt the genesis block
		self.chain.append(genesisBlock)# Initialise the blockchain with the genesis block
	 
	@property
	def lastBlock(self):
		return self.chain[-1] #The last block is the last element in the list

#Note here that it may seem as if the blockchain is mutatable, since a list can be easily edited. However, remember that every subsequent block contains the unique hash of the 
#previous block. If these hashes don't match up, then the blockchain should be disregarded.
#In order to safe guard the blockchain, we must make this process of hashing random via the 'Proof of Work' algorithm. This algorithm specifies some criterion that the hash must
#meet in order for the blockchain to accept a new block. For example, we could introduce an arbitrary constraint that a block in our blockchain must have a hash that begins with
#two zeroes. This hash will stay the same unless the contents of the block are changed, satisfying the immutability requirement.
#To do this, we need to introduce new variables called a 'nonce'and the 'difficulty' of the proof of work algorithm. The difficulty is set to 2 if we require the hash to begin 
#with 2 leading zeroes. The nonce is a variable that will change until the proof of work criterion (the hash having two leading zeroes) is met.
	
	def addBlock(self, block, proof):
		prevHash = self.lastBlock.hash
		if prevHash != block.prevHash:
			return False 
		if not self.isProofValid(block, proof):
			return False
		block.hash = proof
		self.chain.append(block)
		return True
	def proofOfWork(self, block):
		block.nonce = 0 #Variable that changes until PoW is met
		computedHash = block.generate_hash()#Recompute the hash until the PoW is met
		while not computedHash.startswith("0"*Blockchain.difficulty):
			block.nonce += 1
			computedHash = block.generate_hash()
		return computedHash
	def addNewTransaction(self, transaction):
		self.unconfirmedTransactions.append(transaction)
	
	@classmethod
	def isProofValid(cls, block, blockHash):
		return (blockHash.startswith("0"*Blockchain.difficulty) and blockHash == block.generate_hash())#Mining the blockchain
	
	@classmethod
	def checkChainValidity(cls, chain):
		result = True
		preHash = "0"
		for block in chain:
			blockHash = block.hash
            # remove the hash field to recompute the hash again
            # using `generate_hash` method.
			delattr(block, "hash")
			if not cls.isProofValid(block, block.hash) or previous_hash != block.previous_hash:
				result = False
				break
			block.hash, prevHash = blockHash, blockHash
		return result
#An intermediary function between adding the transaction to the block and as such the blockchain; and ensuring PoW is met
	
	def mine(self):
		if not self.unconfirmedTransactions: 
			return False #Checking that the transaction is unconfirmed
		else:
			newBlock = Block(index = self.lastBlock.index +1, transaction = self.unconfirmedTransactions, timestamp = time.time(), prevHash = self.lastBlock.hash) #Check PoW holds for the new block
			proof = self.proofOfWork(newBlock)
			self.addBlock(newBlock, proof)#Clear the unconfirmed transactions list
			self.unconfirmedTransactions = []
			return newBlock.index


# # Creating a web interface and API

# In[5]:


"""
Now we want to create a web interface using Flask in order to mine the 
blockchain
"""

from flask import Flask, request
from flask import render_template, redirect

import requests

app = Flask(__name__)
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"
blockchain = Blockchain()
peers = set()

@app.route('/submit', methods=['POST'])
def submit_textarea():
    """
    Endpoint to create a new transaction via our application.
    """
    post_content = request.form["content"]
    author = request.form["author"]

    post_object = {
        'author': author,
        'content': post_content,
    }

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')


def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')
# In[ ]:

@app.route('/')
def index():
    fetch_posts()
    return render_template('index.html',
                           title='tongyChain: A Decentralized Python app tutorial',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)





#Create a copy of the blockchain for this node


#Create an endpoint to 'POST' to the blockchain



# In[ ]:


"""
Here we creaste an API in order to interact with the blockchain.
Make a 'POST' request using an API (Application Programmable Interface) to the Flask app in order to add the transaction to the network
"""
@app.route('/new_transaction', methods = ['POST'] )
def new_transaction():
    transactionData = request.get_json()
    requiredFields = ["author", "content"]
    for field in requiredFields:
        if not transactionData.get(field):
            return "Invalid transaction data", 404 
            #404 response indicates not found
    transactionData["timestamp"] = time.time()
    blockchain.addNewTransaction(transactionData)
    return "Success", 201

#Now we have created our node, the app's copy of the blockchain. In order to
#increase the security of our blockchain, there would ideally be many copies

"""
Now we make a 'GET' method in order to query and display the blockchain in 
our app
"""

@app.route('/chain', methods = ['GET'])
def getChain():
    chainData = []
    for block in blockchain.chain:
        chainData.append(block.__dict__)
    return json.dumps({"length": len(chainData),
                       "chain": chainData})

"""
We make a 'GET' method in order to query and mine any unconfirmed transactions
that may need adding to the blockchain, in order to give us control over this
"""        

@app.route('/mine', methods = ['GET'])
def mineUnconfirmedTransactions():
    result = blockchain.mine()
    if not result:
        return "There are no transactions to be mined"
    return "Block #{} has been mined".format(result)

"""
We also want to be able to check that there are no unconfirmed transactions.
"""
@app.route('/pendingTransactions')
def getPendingTransactions():
    return json.dumps(blockchain.unconfirmedTransactions)

# endpoint to add new peers to the network.
@app.route('/add_nodes', methods=['POST'])
def registerNewPeers():
    nodes = request.get_json()
    if not nodes:
        return "Invalid data", 400
    for node in nodes:
        peers.add(node)
    return "Success", 201
# In[7]:

"""
We now add the functionality to the API in order to let everyone on the 
network that a block has been mined. As such, everyone should update their
version of the blockchain
"""
#Add the block thats been mined by someone else to your blockchain
@app.route('/add_block', methods = ['POST'])
def validateAndAddBlock():
    #Collect the block the miner just added to the json and then add it to 
    #the blockchain
    blockData = request.get_json()
    block = Block(blockData["index"], blockData["transactions"], 
                 blockData["timestamp"], blockData["prevHash"])
    proof = blockData['hash']
    added = blockchain.addBlock(block, proof)
    
    if not added:
        return 'The block was discarded by the node', 400
    return "The mined block was added to the blockchain", 201





"""
Replace the existing chain with the longest existing train
"""
def consensus():
    global blockchain
    longestChain = None
    currentLength = len(blockchain)
    for node in peers:
        response = requests.get('http://{}/chain'.format(node)) # GET from API
        length = response.json()['length'] #Store the length in a json
        chain = response.json()['chain'] #Store the version of the blockchain
        #in a json
        #Check the longest chain is a valid one
        if length > currentLength and blockchain.checkChainValidity(chain):
            currentLength = length
            longestChain = chain
        #Now if longest chain exists, replace the blockchain with it
        if longestChain:
            blockchain = longestChain
            return True
        #If the longest chain doesn't exist, return False
        return False



def announceNewBlockMined(block):
    for peer in peers: 
        URL = "http://{}/add_block".format(peer)
        requests.post(url, data = json.dumps(block.__dict__, sort_keys = True))
   
def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content.decode('utf-8'))
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["prevHash"]
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['timestamp'],
                       reverse=True)




         
app.run(debug = True)

# # Building and running the web interface

# In[ ]:

