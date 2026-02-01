from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


def generate_schema_cache():
    """Generate schema cache from XSD files."""
    try:
        from json2ubl.core.schema_cache_builder import SchemaCacheBuilder

        builder = SchemaCacheBuilder()
        builder.build_all_caches()
        print("✓ Schema cache generated successfully")
    except Exception as e:
        print(f"⚠ Warning: Failed to generate schema cache: {e}")
        print("  Cache will be generated on first use")


class PostInstallCommand(install):
    """Custom install command that generates schema cache."""

    def run(self):
        install.run(self)
        print("Generating schema cache...")
        generate_schema_cache()


class PostDevelopCommand(develop):
    """Custom develop command that generates schema cache."""

    def run(self):
        develop.run(self)
        print("Generating schema cache...")
        generate_schema_cache()


if __name__ == "__main__":
    setup(
        cmdclass={
            "install": PostInstallCommand,
            "develop": PostDevelopCommand,
        }
    )
