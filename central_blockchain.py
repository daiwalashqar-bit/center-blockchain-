import time
import json
from hashlib import sha256
from flask import Flask, jsonify, request 

class Block:
    def __init__(self, index, transactions, previous_hash, timestamp=None, nonce=0):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()
        self.nonce = nonce
        self.hash = self.compute_hash() 

    def compute_hash(self):
        block_dict = {
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce 
        }
        block_string = json.dumps(block_dict, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    def to_dict(self): 
        return {
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash
        }

class CentralBlockchain:
    def __init__(self, difficulty=2):
        self.chain = []
        self.unconfirmed_transactions = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, ["Genesis Block"], "0")
        genesis.hash = self.proof_of_work(genesis)
        self.chain.append(genesis)

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        prefix = '0' * self.difficulty
        while not computed_hash.startswith(prefix):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)
        return len(self.chain) + 1 

    def mine_block(self):
        if not self.unconfirmed_transactions:
            return None 

        new_block = Block(
            index=self.last_block.index + 1,
            transactions=list(self.unconfirmed_transactions), 
            previous_hash=self.last_block.hash
        )
        
  
        proof = self.proof_of_work(new_block)
        new_block.hash = proof 


        self.chain.append(new_block)
        self.unconfirmed_transactions = [] 
        return new_block.index


    def set_block(self, block):
        if block.previous_hash != self.last_block.hash:
            print("Block previous hash mismatch!")
            return False

        if not block.compute_hash().startswith('0' * self.difficulty):
            print("Block hash does not meet difficulty requirements!")
            return False
        if block.compute_hash() != block.hash: 
            print("Block hash is incorrect!")
            return False

        return True

    def get_block(self, index):
        if 0 <= index < len(self.chain):
            return self.chain[index].to_dict() 
        return None

    def explore_blocks(self):
        return [b.to_dict() for b in self.chain] 

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i-1]
            

            if current.previous_hash != prev.hash:
                return False
            


            if not current.compute_hash().startswith('0' * self.difficulty) or current.compute_hash() != current.hash:
                return False
        return True



app = Flask(__name__)
blockchain = CentralBlockchain(difficulty=3) 



@app.route("/blocks", methods=["GET"])
def list_blocks():
    response = {
        "chain": blockchain.explore_blocks(),
        "length": len(blockchain.chain),
        "is_valid": blockchain.is_chain_valid() 
    }
    return jsonify(response), 200

@app.route("/get_block/<int:index>", methods=["GET"])
def get_block(index):
    block = blockchain.get_block(index)
    if block:
        return jsonify(block), 200
    return jsonify({"error": "Block not found"}), 404

@app.route("/add_transaction", methods=["POST"])
def add_transaction_route():
    payload = request.json or {}
    transaction_data = payload.get("data", "")
    if not transaction_data:
        return jsonify({"error": "Missing 'data' for transaction"}), 400
    
    blockchain.add_transaction(transaction_data)
    response = {"message": "Transaction will be added to the next mined block."}
    return jsonify(response), 201

@app.route("/mine_block", methods=["POST"]) 
def mine_block_route():
    mined_block_index = blockchain.mine_block()
    if mined_block_index is not None:
        block = blockchain.get_block(mined_block_index)
        response = {
            "message": "New block mined!",
            "block": block
        }
        return jsonify(response), 201
    else:
        response = {"message": "No unconfirmed transactions to mine."}
        return jsonify(response), 200 

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "length": len(blockchain.chain),
        "difficulty": blockchain.difficulty,
        "latest_hash": blockchain.last_block.hash if blockchain.chain else "N/A",
        "unconfirmed_transactions_count": len(blockchain.unconfirmed_transactions),
        "is_chain_valid": blockchain.is_chain_valid()
    }), 200

@app.route("/check_validity", methods=["GET"])
def check_validity():
    is_valid = blockchain.is_chain_valid()
    response = {"is_chain_valid": is_valid, "message": "Blockchain is valid." if is_valid else "Blockchain is NOT valid!"}
    return jsonify(response), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)