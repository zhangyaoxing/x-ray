class Version():
    def __init__(self, version_array):
        if not isinstance(version_array, list) or len(version_array) > 4:
            raise ValueError("Invalid version array")
        while len(version_array) < 4:
            version_array.append(0)
        self.version_array = version_array

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.version_array < other.version_array
    def __le__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.version_array <= other.version_array
    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.version_array == other.version_array
    def __ne__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.version_array != other.version_array
    def __gt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.version_array > other.version_array
    def __ge__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.version_array >= other.version_array
    def __str__(self):
        # Only output first 3 parts
        version_array = self.version_array[:3]
        return ".".join(str(x) for x in version_array)
    def __repr__(self):
        return f"Version({self.version_array})"
    def compatible_with(self, version) -> bool:
        """Check if the given version is compatible with this version."""
        # If the major and minor version are the same, consider compatible
        if self.version_array[0] == version.version_array[0] and self.version_array[1] == version.version_array[1]:
            return True
        return False
    def to_compatibility_str(self) -> str:
        return f"{self.version_array[0]}.{self.version_array[1]}"
    
    def parse(version_str):
        parts = version_str.split(".")
        version_array = []
        for part in parts:
            try:
                version_array.append(int(part))
            except ValueError:
                version_array.append(0)
        return Version(version_array)