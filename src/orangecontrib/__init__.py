# __path__ = __import__('pkgutil').extend_path(__path__, __name__)

# setuptools wants this...
__import__('pkg_resources').declare_namespace(__name__)
