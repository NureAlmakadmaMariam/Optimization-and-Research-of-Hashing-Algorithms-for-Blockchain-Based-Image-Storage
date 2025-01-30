from flask import Flask, request, jsonify
from entities.blockchain import Blockchain
import hashlib
import time
import zipfile
import io
import matplotlib.pyplot as plt
import os
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
blockchain = Blockchain()

@app.route('/plot_creation_times', methods=['GET'])
def plot_creation_times():
    metadata = blockchain.get_block_metadata()

    if not metadata:
        return jsonify({'message': 'No block metadata available to plot'}), 404

    plot_path = plot_block_creation_times(metadata)
    return jsonify({'message': 'Plot created successfully', 'plot_url': f'/{plot_path}'})

def plot_block_creation_times(data):
    block_indices = [item['block_index'] for item in data]
    creation_times = [item['creation_time'] for item in data]

    plt.figure(figsize=(10, 6))
    plt.plot(block_indices, creation_times, marker='o', color='b', label='Creation Time')
    plt.title('Block Creation Times')
    plt.xlabel('Block Index')
    plt.ylabel('Creation Time (s)')
    plt.grid(True)
    plt.legend()

    if not os.path.exists('static'):
        os.makedirs('static')
    plot_path = 'static/block_creation_times.png'
    plt.savefig(plot_path)
    plt.close()

    return plot_path


def hash_picture(picture, algorithm):
    if algorithm == 'sha256':
        return hashlib.sha256(picture.read()).hexdigest()
    elif algorithm == 'blake2':
        return hashlib.blake2b(picture.read()).hexdigest()
    return None

@app.route('/add_block_zip_parallel', methods=['POST'])
def add_block_zip_parallel():
    algorithm = request.args.get('algorithm', '').lower()
    if algorithm not in ['sha256', 'blake2']:
        return jsonify({'message': 'Invalid algorithm. Use "sha256" or "blake2"'}), 400

    zip_file = request.files.get('archive')
    if not zip_file:
        return jsonify({'message': 'No ZIP file provided'}), 400

    pictures = []
    try:
        with zipfile.ZipFile(zip_file) as zf:
            for file_name in zf.namelist():
                with zf.open(file_name) as file:
                    pictures.append(io.BytesIO(file.read()))
    except zipfile.BadZipFile:
        return jsonify({'message': 'Invalid ZIP file'}), 400

    chunks = [pictures[i:i + 10] for i in range(0, len(pictures), 10)]
    block_creation_times = []

    for chunk in chunks:
        start_time = time.time()

        with ThreadPoolExecutor() as executor:
            picture_hashes = list(executor.map(lambda pic: hash_picture(pic, algorithm), chunk))

        previous_block = blockchain.chain[-1]
        if not previous_block.proof:
            return jsonify({'message': 'Mine a block first to establish proof of work'}), 400

        previous_hash = previous_block.block_hash
        previous_proof = previous_block.proof
        proof = blockchain.proof_of_work(previous_proof)

        new_block = blockchain.create_block(proof, previous_hash, picture_hashes, algorithm)

        end_time = time.time()
        creation_time = end_time - start_time

        blockchain.save_block_metadata(new_block.index, creation_time, algorithm)
        block_creation_times.append({
            'block_index': new_block.index,
            'creation_time': creation_time,
            'algorithm': algorithm
        })

    response = {
        'message': 'Blocks created successfully',
        'blocks': block_creation_times
    }
    return jsonify(response), 201

@app.route('/add_block_zip', methods=['POST'])
def add_block_zip():
    algorithm = request.args.get('algorithm', '').lower()
    if algorithm not in ['sha256', 'blake2']:
        return jsonify({'message': 'Invalid algorithm. Use "sha256" or "blake2"'}), 400

    zip_file = request.files.get('archive')
    if not zip_file:
        return jsonify({'message': 'No ZIP file provided'}), 400

    pictures = []
    try:
        with zipfile.ZipFile(zip_file) as zf:
            for file_name in zf.namelist():
                with zf.open(file_name) as file:
                    pictures.append(io.BytesIO(file.read()))
    except zipfile.BadZipFile:
        return jsonify({'message': 'Invalid ZIP file'}), 400

    chunks = [pictures[i:i + 10] for i in range(0, len(pictures), 10)]
    block_creation_times = []

    for chunk in chunks:
        picture_hashes = []

        start_time = time.time()

        for picture in chunk:
            if algorithm == 'sha256':
                picture_hashes.append(hashlib.sha256(picture.read()).hexdigest())
            elif algorithm == 'blake2':
                picture_hashes.append(hashlib.blake2b(picture.read()).hexdigest())

        previous_block = blockchain.chain[-1]
        if not previous_block.proof:
            return jsonify({'message': 'Mine a block first to establish proof of work'}), 400

        previous_hash = previous_block.block_hash
        previous_proof = previous_block.proof
        proof = blockchain.proof_of_work(previous_proof)

        new_block = blockchain.create_block(proof, previous_hash, picture_hashes, algorithm)

        end_time = time.time()
        creation_time = end_time - start_time

        blockchain.save_block_metadata(new_block.index, creation_time, algorithm)
        block_creation_times.append({
            'block_index': new_block.index,
            'creation_time': creation_time,
            'algorithm': algorithm
        })

    response = {
        'message': 'Blocks created successfully',
        'blocks': block_creation_times
    }
    return jsonify(response), 201



@app.route('/add_block', methods=['POST'])
def add_block():
    start_time = time.time()
    algorithm = request.args.get('algorithm').lower()

    pictures = request.files.getlist('Pictures')
    picture_hash = []

    for picture in pictures:
        if algorithm == 'sha256':
            picture_hash.append(hashlib.sha256(picture.read()).hexdigest())
        elif algorithm == 'blake2':
            picture_hash.append(hashlib.blake2b(picture.read()).hexdigest())
        else:
            return jsonify({'message': f'Unsupported hash algorithm: {algorithm}'}), 400

    previous_block = blockchain.chain[-1]
    if not previous_block.proof:
        response = {'message': 'Mine a block first to establish proof of work'}
        return jsonify(response), 400

    previous_hash = previous_block.block_hash

    previous_proof = previous_block.proof
    proof = blockchain.proof_of_work(previous_proof)
    new_block = blockchain.create_block(proof, previous_hash, picture_hash, algorithm)

    end_time = time.time()  # Кінець вимірювання часу
    execution_time = end_time - start_time  # Час роботи

    if new_block:
        response = {
            'message': 'Pictures added and a block is MINED',
            'index': new_block.index,
            'timestamp': new_block.timestamp,
            'proof': new_block.proof,
            'previous_hash': new_block.previous_hash,
            'hash': new_block.block_hash,
            'picture_hash': new_block.picture_hash,
            'algorithm': algorithm,
            'execution_time': round(execution_time, 4)  # Виводимо час роботи у секундах
        }
        return jsonify(response), 201
    else:
        response = {'message': 'Error adding block'}
        return jsonify(response), 500

@app.route('/search_picture', methods=['GET'])
def search_picture():
    picture = request.files.getlist('Picture')[0]

    picture.seek(0)
    sha256_hash = hashlib.sha256(picture.read()).hexdigest()

    picture.seek(0)
    blake2_hash = hashlib.blake2b(picture.read()).hexdigest()

    if not sha256_hash or not blake2_hash:
        response = {'message': 'Hash computation failed'}
        return jsonify(response), 400

    result = blockchain.search_picture_hash(sha256_hash, blake2_hash)

    return jsonify(result), 200 if 'found' in result['message'].lower() else 400

@app.route('/get_chain', methods=['GET'])
def display_chain():
    response = {'chain': [block.__dict__ for block in blockchain.chain],
                'length': len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/valid', methods=['GET'])
def valid():
    if blockchain.chain_valid():
        response = {'message': 'The Blockchain is valid.'}
    else:
        response = {'message': 'The Blockchain is not valid.'}
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)

