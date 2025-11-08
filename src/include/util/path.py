"""Utility functions for file system path operations."""

import os
from typing import TypedDict


class DirectoryTree(TypedDict):
    """Type definition for directory tree structure."""
    files: list[str]
    dirs: dict[str, 'DirectoryTree']


async def build_directory_tree(root_path: str) -> DirectoryTree:
    """
    Build a nested directory tree structure from a root path.
    
    Recursively scans the directory structure and returns a dictionary
    containing files and subdirectories.
    
    Args:
        root_path: Root directory path to scan
        
    Returns:
        Dictionary with 'files' (list of file names) and 'dirs' (nested directories)
        
    Example:
        >>> tree = await build_directory_tree("/path/to/dir")
        >>> tree
        {'files': ['file1.txt', 'file2.txt'], 'dirs': {'subdir': {...}}}
    """
    def build_tree(path: str) -> DirectoryTree:
        tree: DirectoryTree = {"files": [], "dirs": {}}
        
        try:
            for entry in os.scandir(path):
                if entry.is_dir():
                    tree["dirs"][entry.name] = build_tree(os.path.join(path, entry.name))
                elif entry.is_file():
                    tree["files"].append(entry.name)
        except PermissionError:
            # Skip directories we don't have permission to read
            pass
            
        return tree

    return build_tree(root_path)
