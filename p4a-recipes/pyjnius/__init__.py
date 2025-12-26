from pythonforandroid.recipes.pyjnius import PyjniusRecipe


class PyjniusPython3Recipe(PyjniusRecipe):
    """
    Custom pyjnius recipe with Python 3 compatibility patch.
    Fixes the 'long' type issue in jnius_utils.pxi.
    """

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)

        # Apply Python 3 compatibility patch
        import os
        utils_file = os.path.join(self.get_build_dir(arch.arch), 'jnius', 'jnius_utils.pxi')

        if os.path.exists(utils_file):
            print("[UDAC] Patching jnius_utils.pxi for Python 3 compatibility...")

            with open(utils_file, 'r') as f:
                content = f.read()

            # Fix the 'long' type issue - remove Python 2 long check
            content = content.replace(
                "if isinstance(arg, int) or (\n                    (isinstance(arg, long) and arg < 2147483648)):",
                "if isinstance(arg, int):"
            )

            with open(utils_file, 'w') as f:
                f.write(content)

            print("[UDAC] Python 3 patch applied successfully!")


recipe = PyjniusPython3Recipe()
