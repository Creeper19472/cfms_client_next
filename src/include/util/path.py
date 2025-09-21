import os


async def build_directory_tree(root_path):
    def build_tree(path):
        tree = {"files": [], "dirs": {}}
        for entry in os.scandir(path):
            if entry.is_dir():
                tree["dirs"][entry.name] = build_tree(
                    os.path.join(path, entry.name)
                )
            elif entry.is_file():
                tree["files"].append(entry.name)
        return tree

    return build_tree(root_path)