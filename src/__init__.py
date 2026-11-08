# To make API as easy as possible, we will keep files in API package and abstract to the user
# in src/__init__.py, do "from .api.main import func, anotherFunc" for example,
# so users can write "import vistool" instead of "import vistool.api.main"