from pythonforandroid.recipes.kivy import KivyRecipe
import re


class KivyPython3Recipe(KivyRecipe):
    """
    Custom Kivy recipe with Python 3 compatibility patch.
    Fixes 'long' type issues in Kivy source files.
    """

    def build_arch(self, arch):
        """Override build_arch to patch BEFORE Cython runs."""

        # Apply patches FIRST, before calling super()
        self.apply_python3_patches(arch)

        # Now run the normal build
        super().build_arch(arch)

    def apply_python3_patches(self, arch):
        """Apply Python 3 compatibility patches to all Kivy source files."""
        import os
        import glob

        build_dir = self.get_build_dir(arch.arch)
        kivy_dir = os.path.join(build_dir, 'kivy')

        if not os.path.exists(kivy_dir):
            print(f"[UDAC] Warning: kivy directory not found at {kivy_dir}")
            return

        # Patch all .pyx files
        source_files = glob.glob(os.path.join(kivy_dir, '**/*.pyx'), recursive=True)

        print(f"[UDAC] Patching {len(source_files)} Kivy source files for Python 3 compatibility...")
        total_replacements = 0

        for source_file in source_files:
            with open(source_file, 'r') as f:
                content = f.read()

            original_content = content

            # Remove __long__ methods entirely (not needed in Python 3)
            content = re.sub(
                r'^\s*def __long__\(self\):.*?^(?=\s*def\s|\s*cdef\s|$)',
                '',
                content,
                flags=re.MULTILINE | re.DOTALL
            )

            # Replace any remaining long() calls with int()
            content = re.sub(r'\blong\(', 'int(', content)

            if content != original_content:
                replacements = original_content.count('long') - content.count('long')
                with open(source_file, 'w') as f:
                    f.write(content)
                relative_path = os.path.relpath(source_file, build_dir)
                print(f"[UDAC]   ✓ {relative_path}: {replacements} 'long' occurrences removed")
                total_replacements += replacements

        if total_replacements > 0:
            print(f"[UDAC] Kivy Python 3 patch applied successfully! Total replacements: {total_replacements}")
        else:
            print("[UDAC] No 'long' types found in Kivy - already patched or different version")


recipe = KivyPython3Recipe()
