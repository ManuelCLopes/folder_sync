import os
import sys
import time
import shutil
import logging
import signal

CHUNK_SIZE = 1024 * 1024  # 1 MB
shutdown_flag = False  # Flag to handle shutdown

def setup_logging(log_file):
    # Set up logging to file and console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_directories(source_root, replica_root):
    # Create directories in replica to match those in the source
    for root, dirs, _ in os.walk(source_root):
        rel_path = os.path.relpath(root, source_root)
        replica_dir_root = os.path.join(replica_root, rel_path)
        
        for dir_name in dirs:
            replica_dir = os.path.join(replica_dir_root, dir_name)
            try:
                if not os.path.exists(replica_dir):
                    os.makedirs(replica_dir)
                    logging.info(f"Directory created: {replica_dir}")
            except OSError as e:
                logging.error(f"Failed to create directory {replica_dir}: {e}")

def copy_file_in_chunks(source_file, replica_file):
    # Copy large files in chunks to prevent memory overload
    try:
        with open(source_file, 'rb') as src, open(replica_file, 'wb') as dst:
            shutil.copyfileobj(src, dst, length=CHUNK_SIZE)
        logging.info(f"File copied: {source_file} -> {replica_file}")
    except (OSError, IOError) as e:
        logging.error(f"Error copying file {source_file}: {e}")

def copy_or_update_files(source_root, replica_root):
    # Copy or update files from source to replica
    for root, _, files in os.walk(source_root):
        rel_path = os.path.relpath(root, source_root)
        replica_dir_root = os.path.join(replica_root, rel_path)
        
        for file_name in files:
            source_file = os.path.join(root, file_name)
            replica_file = os.path.join(replica_dir_root, file_name)

            try:
                if not os.path.exists(replica_file):
                    # If file doesn't exist, copy it in chunks
                    copy_file_in_chunks(source_file, replica_file)
                else:
                    # Check the last modified times
                    source_mtime = os.path.getmtime(source_file)
                    replica_mtime = os.path.getmtime(replica_file)

                    if source_mtime > replica_mtime:
                        # If the source file is newer, update the replica
                        copy_file_in_chunks(source_file, replica_file)
                        logging.info(f"File updated: {source_file} -> {replica_file}")
            except (OSError, IOError) as e:
                logging.error(f"Error copying/updating file {source_file}: {e}")

def delete_extra_files_and_dirs(source_root, replica_root):
    # Delete files and directories from replica that no longer exist in source
    for root, dirs, files in os.walk(replica_root, topdown=False):
        rel_path = os.path.relpath(root, replica_root)
        source_dir_root = os.path.join(source_root, rel_path)

        for file_name in files:
            replica_file = os.path.join(root, file_name)
            source_file = os.path.join(source_dir_root, file_name)

            try:
                if not os.path.exists(source_file):
                    os.remove(replica_file)
                    logging.info(f"File removed: {replica_file}")
            except OSError as e:
                logging.error(f"Failed to remove file {replica_file}: {e}")

        for dir_name in dirs:
            replica_dir = os.path.join(root, dir_name)
            source_dir = os.path.join(source_dir_root, dir_name)

            try:
                if not os.path.exists(source_dir):
                    shutil.rmtree(replica_dir)
                    logging.info(f"Directory removed: {replica_dir}")
            except OSError as e:
                logging.error(f"Failed to remove directory {replica_dir}: {e}")

def sync_folders(source, replica):
    # Main function to synchronize source to replica
    try:
        if not os.path.exists(replica):
            os.makedirs(replica)
            logging.info(f"Replica directory created: {replica}")
    except OSError as e:
        logging.error(f"Failed to create replica directory {replica}: {e}")
        return

    create_directories(source, replica)
    copy_or_update_files(source, replica)
    delete_extra_files_and_dirs(source, replica)

def handle_signal(signal_received, frame):
    global shutdown_flag
    logging.info("Received termination signal. Shutting down sync process...")
    shutdown_flag = True

def main():
    global shutdown_flag

    # Check if the correct number of arguments is provided
    if len(sys.argv) != 5:
        print("Usage: python sync_folders.py <source_folder> <replica_folder> <sync_interval> <log_file>")
        sys.exit(1)

    source_folder = sys.argv[1]
    replica_folder = sys.argv[2]
    sync_interval = int(sys.argv[3])
    log_file = sys.argv[4]

    if not os.path.exists(source_folder):
        print(f"Source folder {source_folder} does not exist.")
        sys.exit(1)

    setup_logging(log_file)

    # Set up signal handlers for shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while not shutdown_flag:
        try:
            sync_folders(source_folder, replica_folder)
        except Exception as e:
            logging.error(f"Unexpected error during sync: {e}")
        time.sleep(sync_interval)

    logging.info("Sync process terminated.")

if __name__ == "__main__":
    main()
