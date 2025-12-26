from pythonforandroid.recipes.pyjnius import PyjniusRecipe
import re


class PyjniusPython3Recipe(PyjniusRecipe):
    """
    Custom pyjnius recipe with Python 3 compatibility patch.
    Fixes ALL 'long' type issues in jnius_utils.pxi.
    """

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)

        # Apply Python 3 compatibility patch to ALL pyjnius source files
        import os
        import glob

        build_dir = self.get_build_dir(arch.arch)
        jnius_dir = os.path.join(build_dir, 'jnius')

        if not os.path.exists(jnius_dir):
            print(f"[UDAC] Warning: jnius directory not found at {jnius_dir}")
            return

        # Patch all .pxi and .pyx files
        source_files = glob.glob(os.path.join(jnius_dir, '*.pxi')) + glob.glob(os.path.join(jnius_dir, '*.pyx'))

        print(f"[UDAC] Patching {len(source_files)} pyjnius source files for Python 3 compatibility...")
        total_replacements = 0

        for source_file in source_files:
            with open(source_file, 'r') as f:
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
                replacements = original_content.count('long') - content.count('long')
                with open(source_file, 'w') as f:
                    f.write(content)
                print(f"[UDAC]   ✓ {os.path.basename(source_file)}: {replacements} 'long' occurrences removed")
                total_replacements += replacements

        if total_replacements > 0:
            print(f"[UDAC] Python 3 patch applied successfully! Total replacements: {total_replacements}")
        else:
            print("[UDAC] No 'long' types found - already patched or different version")


recipe = PyjniusPython3Recipe()

