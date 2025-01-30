import datetime
import hashlib

import psycopg2
from psycopg2.extras import RealDictCursor

from entities.block import Block

DB_NAME = "lab3"
DB_USER = "postgres"
DB_PASSWORD = "admin123"
DB_HOST = "localhost"
DB_PORT = "5432"

class Blockchain:
    def __init__(self):

        self.conn = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        # Create a cursor
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                id SERIAL PRIMARY KEY,
                index INTEGER,
                timestamp TIMESTAMP,
                proof INTEGER,
                previous_hash TEXT,
                block_hash TEXT,
                picture_hash TEXT[]
            )
        ''')
        self.conn.commit()

        self.load_blocks_from_db()

        if len(self.chain) == 0:
            self.create_block(proof=1, previous_hash='0', picture_hash=[], algorithm='sha256')

    def load_blocks_from_db(self):
        self.cursor.execute("SELECT * FROM blocks ORDER BY id")
        rows = self.cursor.fetchall()

        self.chain = [Block(**row) for row in rows]

    def create_block(self, proof, previous_hash, picture_hash, algorithm):
        block = Block(index=len(self.chain) + 1,
                      timestamp=str(datetime.datetime.now()),
                      proof=proof,
                      previous_hash=previous_hash,
                      picture_hash=picture_hash)

        if algorithm == 'sha256':
            block.block_hash = block.hash_sha256()
        else:
            block.block_hash = block.hash_blake2b()

        self.save_block_to_db(block)
        self.chain.append(block)
        return block

    def search_picture_hash(self, target_hash_sha256, target_hash_blake2):
        for block in reversed(self.chain):
            for hash in block.picture_hash:
                if hash == target_hash_sha256:
                    return {'message': 'Picture hash found using SHA-256 in block', 'block_index': block.index}

            for hash in block.picture_hash:
                if hash == target_hash_blake2:
                    return {'message': 'Picture hash found using Blake2 in block', 'block_index': block.index}

        return {'message': 'Picture hash not found in the blockchain'}

    def save_block_to_db(self, block):
        self.cursor.execute('''
            INSERT INTO blocks (index, timestamp, proof, previous_hash, picture_hash, block_hash)
            VALUES (%s, %s, %s, %s, %s::text[], %s)
        ''', (block.index, block.timestamp, block.proof, block.previous_hash, block.picture_hash, block.block_hash))

        self.conn.commit()

    def save_block_metadata(self, block_index, creation_time, algorithm):
        self.cursor.execute('''
            INSERT INTO block_metadata (block_index, creation_time, algorithm)
            VALUES (%s, %s, %s)
        ''', (block_index, creation_time, algorithm))
        self.conn.commit()

    def get_block_metadata(self):
        self.cursor.execute("SELECT block_index, creation_time FROM block_metadata ORDER BY block_index")
        return self.cursor.fetchall()


    def print_previous_block(self):
        if len(self.chain) > 0:
            return self.chain[-1]
        return None

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False

        while check_proof is False:
            hash_operation = hashlib.sha256(
                str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:5] == '00000':
                check_proof = True
            else:
                new_proof += 1

        return new_proof

    def chain_valid(self):

        if len(self.chain) < 2:
            return {'valid': True, 'message': "Blockchain is valid (only genesis block exists)."}

        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.previous_hash != previous_block.block_hash:
                return {
                    'valid': False,
                    'message': f"Blockchain is invalid: Block {current_block.index} has mismatched previous_hash."
                }

        return {'valid': True, 'message': "Blockchain is valid."}

    def __del__(self):
        self.cursor.close()
        self.conn.close()