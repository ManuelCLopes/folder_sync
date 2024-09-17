# Folder Sync Utility

## Overview

The Folder Sync Utility is a Python program designed to synchronize the contents of a source folder with a replica folder. It ensures that the replica folder is an exact mirror of the source folder by copying new files, updating modified files, and deleting files that no longer exist in the source folder.

## Features

- One-way synchronization from the source folder to the replica folder.
- Automatically creates, updates, or deletes files and directories to maintain an exact replica.
- Uses last modification times to avoid unnecessary file updates.
- Logs all operations (file creation, updates, and deletion) to a log file and the console.
- Periodically runs the synchronization based on a user-specified interval.

## Usage

### Command Line Arguments

```bash
python sync_folders.py <source_folder> <replica_folder> <sync_interval> <log_file>
