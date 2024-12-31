from pathlib import Path
import hashlib
import pickle

def get_all_files(directory):
    return [f for f in directory.rglob('*') if f.is_file() and f.name != Path(__file__).name]

def compute_md5(file_path):
    md5_hash = hashlib.md5()
    try:
        with file_path.open("rb") as f:
            print(f"Calculating MD5 for {file_path.name}")
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except Exception as e:
        print(f"Error calculating MD5 for {file_path}: {e}")
        return None

def generate_file_hashes(directory):
    files = get_all_files(directory)
    file_hash_list = []
    for file_path in files:
        md5 = compute_md5(file_path)
        if md5:
            rel_path = file_path.relative_to(directory)
            file_size = file_path.stat().st_size
            file_hash_list.append((str(rel_path), md5, file_size))
    return file_hash_list

if __name__ == "__main__":
    directory = Path("D:\\setup_input\\sakura")
    hashes = generate_file_hashes(directory)
    with open("file_hashes.bin", "wb") as f:
        pickle.dump(hashes, f)
