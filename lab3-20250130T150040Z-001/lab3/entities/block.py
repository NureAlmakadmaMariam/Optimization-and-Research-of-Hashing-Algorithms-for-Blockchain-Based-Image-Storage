import hashlib
import json

class Block:
    def __init__(self, **kwargs):
        self.index = kwargs.get('index')
        self.timestamp = kwargs.get('timestamp')
        self.proof = kwargs.get('proof')
        self.previous_hash = kwargs.get('previous_hash')
        self.picture_hash = kwargs.get('picture_hash')
        self.block_hash = kwargs.get('block_hash', self.hash_sha256())

    def hash_sha256(self) -> str:

        encoded_block = json.dumps(self.__dict__, sort_keys=True, default=str).encode()
        sha256_hash = hashlib.sha256(encoded_block).hexdigest()
        return sha256_hash

    def hash_blake2b(self) -> str:

        encoded_block = json.dumps(self.__dict__, sort_keys=True, default=str).encode()
        blake2b_hash = hashlib.blake2b(encoded_block).hexdigest()
        return blake2b_hash

