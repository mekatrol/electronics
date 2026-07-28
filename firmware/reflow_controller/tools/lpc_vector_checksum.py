#!/usr/bin/env python3
"""Write the LPC17xx vector-table checksum into a raw firmware image."""

import struct
import sys


def main() -> None:
    image_path = sys.argv[1]
    with open(image_path, "r+b") as image:
        vectors = struct.unpack("<8I", image.read(32))
        checksum = (-sum(vectors[:7])) & 0xFFFFFFFF
        image.seek(28)
        image.write(struct.pack("<I", checksum))


if __name__ == "__main__":
    main()
