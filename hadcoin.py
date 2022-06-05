# create Crypto currency
# requests==2.18.4
import datetime
import hashlib
import json
from flask import Flask,jsonify,request
import requests
from uuid import uuid4
from urllib.parse import urlparse

#part1 building blockchain

class Blockchain:
    #intilialise the genesys block
    def __init__(self):
        #chain is list of blocks
        self.chain = []
        #intialising mempool ie tranactions
        self.transactions=[]
        #creating a genesys block
        self.create_block(proof=1,previous_hash='0')
        # nodes
        self.nodes=set()
        
    

        
    def create_block(self,proof,previous_hash):
        block = {'index':len(self.chain)+1,
                 'timestamp':str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash':previous_hash,
                 'transactions':self.transactions}
        self.transactions=[]
        self.chain.append(block)
        
        return block
    
    def get_previous_block(self):
        #return last block
        return self.chain[-1]
    
    
    def proof_of_work(self,previous_proof):
        new_proof = 1
        check_proof=False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            #here sha256 takes new proof and previous proof and do an 
            #operation basically ay Asymmetric operation
            # check if hasoperation has 4 leading zeros
            
            if hash_operation[:4]=="0000":
                check_proof=True
            else:
                new_proof += 1
                
                
        return new_proof
    
    #this fucton returns sha256 value for a block
    def hash(self,block):
        
        #use json to make a object into a string using dumps function
        #because sha256 only works on strings
        encoded_block = json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    #if each node is correct this fuction returns true and if anything
    # is wrong it just prints false ie block chain is not good
    # in this we check two things 1. if previous hash is same as previous hash used in the current block 
    #2. Is the proof of each block is valid according to proof_of_work function
    def is_chain_valid(self,chain):
        previous_block = chain[0]
        block_index=1
        while block_index<len(chain):
            block=chain[block_index]
            if block['previous_hash']!= self.hash(previous_block):
                return False
            previous_proof=previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            
            if hash_operation[:4] != "0000":
                return False
            
            previous_block = block
            block_index +=1
        
        return True
    
    
    def add_transaction(self,sender,receiver,amount):
        self.transactions.append({'sender':sender,
                                  'receiver':receiver,
                                  'amount':amount})
        # here we are returnin the block in which the tranaction goes
        previous_block = self.get_previous_block()
        return previous_block['index']+1
    
    
    def add_node(self,address):
        parsed_url=urlparse(address)
        set.nodes.add(parsed_url.netloc)
        #parsed_url will give dictonary where netloc as key contain address and port number
    
    
    def replace_chain(self):
        network= self.nodes
        longest_chain=None
        max_length = len(self.chain)
        
        for node in network:
            #now we use requests library to get chain lengthin each node
            response = requests.get(f 'http://{node}/get_chain')
            #here we used get_chain method which gives chainlength and chain also
            if response.status_code == 200:
               length= response.json()['length']
               chain = response.json()['chain']
               
               if length>max_length and (self.is_chain_valid(chain)):
                   max_length=length
                   longest_chain=chain
                   
        # this if loop executes if longest chain in changed ie not NOne           
        if longest_chain:
            self.chain=longest_chain
            return True
                
        return False
        
    
    
#part2 mining block_chain 

# create webapp using Flask

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

## creating an address for the node on Port 5000
# the resoan for this address is when miner mines a new block then he is going
# to get btcoins from this address
# uuid4 will generate unqiue address  and it contain hyphens too.so we replace them

node_address = str(uuid4()).replace('-','')
#this will be adress fo node in port 5000

#create blockchain

blockchain = Blockchain()

#mining a new block

@app.route('/mine_block',methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    # this tranaction is added as gift to miner Hadlein for mining a new block
    blockchain.add_transaction(sender=node_address,receiver='Hadelin',amount=1)
    
    block = blockchain.create_block(proof,previous_hash)
    response={'message':'You just mined a block.','index':block['index'],
                 'timestamp':block['timestamp'],
                 'proof': block['proof'],
                 'previous_hash':block['previous_hash'],
                 'transactions':block['transactions']}
    
    return jsonify(response),200
# here we used 200 which is http code for sucess


# getting the full block chain displayed 
@app.route('/get_chain',methods=['GET'])
def get_chain():
    response = {'chain':blockchain.chain,
                'length': len(blockchain.chain)}
    
    return jsonify(response),200
# checking if block chain is valid
@app.route('/is_valid',methods=['GET'])
def is_valid():
    
    valid = blockchain.is_chain_valid(blockchain.chain)
    if valid:
        response={'message':'You block chain is perfect'}
    else:
        response={'message':'You block chain is not correct'}
        
    
    return jsonify(response),200
# here we used 200 which is http code for sucess




# adding a new tranaction to the Blockchain
@app.route('/add_transaction',methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys=['sender','receiver','amount']
    #checkig if tranaction contains all keys
    if not all (key in json for key in transaction_keys):
        return 'Some elements of transactions are missing',400
    
    index = blockchain.add_transaction(json['sender'],json['receiver'],json['amount'])
    response = {'messege':f 'This transaction will be added to block {index}'}
    return jsonify(response),201



# part3 decentralising our blockchain

#connecting new nodes
# adding a new tranaction to the Blockchain
@app.route('/connect_node',methods=['POST'])
def connect_node():
    json = request.get_json()
    #nodes val contain array of nodes to be added into blockchain
    nodes=json.get('nodes')
    if nodes is None:
        return "No node",400
    
    for node in nodes:
        blockchain.add_node(node)
    
    # addeed all nodes to blockchain
    
    response = {'message':'All the nodes are connected',
                'total_nodes':list(blockchain.nodes)
                }
    
    return jsonify(response),201


# replacing chain by longest chain if needed

@app.route('/replace_chain',methods=['GET'])
def replace_chain():
    
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response={'message':'The blockchain is upto date',
                  'new_chain':blockchain.chain}
    else:
        response={'message':'You block chain is not up to date.So,replaced to largest chain',
                  'new_chain':blockchain.chain}
        
    
    return jsonify(response),200
# here we used 200 which is http code for sucess
    






#Running the app
app.run(host='0.0.0.0',port=5000)
    
    
        
        
        
        
        
        
