__all__ = ["get_parent_route"]


def get_parent_route(route: str) -> str:
    result = route.rstrip('/').rsplit('/', 1)[0] or '/home'
    return result


if __name__ == "__main__":
    print(get_parent_route("/foo/bar/"))
    print(get_parent_route("/foo/bar"))
    print(get_parent_route("/foo/"))
    print(get_parent_route("/foo"))
    print(get_parent_route("/"))
