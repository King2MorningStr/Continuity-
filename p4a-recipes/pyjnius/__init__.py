from pythonforandroid.recipes.pyjnius import PyjniusRecipe
import re


class PyjniusPython3Recipe(PyjniusRecipe):
    """
    Custom pyjnius recipe with Python 3 compatibility patch.
    Fixes ALL 'long' type issues in jnius_utils.pxi.
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

            original_content = content

            # Fix ALL 'long' type issues - replace all isinstance checks
            # Pattern 1: isinstance(arg, long)
            content = re.sub(r'\bisinstance\([^,]+,\s*long\)', 'False', content)

            # Pattern 2: or isinstance(arg, long) - just remove the check
            content = re.sub(r'\s+or\s+isinstance\([^,]+,\s*long\)', '', content)

            # Pattern 3: isinstance(arg, int) or (isinstance(arg, long) and ...) - simplify to just int check
            content = re.sub(
                r'isinstance\(([^,]+),\s*int\)\s+or\s+\(\s*isinstance\(\1,\s*long\)[^)]*\)',
                r'isinstance(\1, int)',
                content
            )

            if content != original_content:
                with open(utils_file, 'w') as f:
                    f.write(content)
                print("[UDAC] Python 3 patch applied successfully!")
                print(f"[UDAC] Replaced {original_content.count('long') - content.count('long')} occurrences of 'long'")
            else:
                print("[UDAC] No 'long' types found - already patched or different version")


recipe = PyjniusPython3Recipe()

