#!/usr/bin/env python
#
# Copyright (C) 2016 The CyanogenMod Project
# Copyright (C) 2017-2020 The LineageOS Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys
import argparse
from hashlib import sha1
from typing import List, Tuple


class SHA1Updater:
    def __init__(
        self, device: str, vendor: str, proprietary_file: str = "proprietary-files.txt"
    ):
        self.device = device
        self.vendor = vendor
        self.proprietary_file = proprietary_file
        self.vendor_path = os.path.join(
            "..", "..", "..", "vendor", vendor, device, "proprietary"
        )
        self.lines: List[str] = []

    def read_proprietary_files(self) -> None:
        """Read the proprietary files list."""
        try:
            with open(self.proprietary_file, "r") as f:
                self.lines = f.read().splitlines()
        except FileNotFoundError:
            print(f"Error: {self.proprietary_file} not found")
            sys.exit(1)

    def write_proprietary_files(self) -> None:
        """Write back the modified proprietary files list."""
        try:
            with open(self.proprietary_file, "w") as f:
                f.write("\n".join(self.lines) + "\n")
        except IOError as e:
            print(f"Error writing to {self.proprietary_file}: {e}")
            sys.exit(1)

    def process_line(self, line: str, need_sha1: bool) -> Tuple[str, bool]:
        """Process a single line and update SHA1 if needed."""
        # Skip empty lines
        if not line:
            return line, need_sha1

        # Check if we need to set SHA1 hash for the next files
        if line[0] == "#":
            return line, " - from" in line

        if not need_sha1:
            return line, need_sha1

        # Remove existing SHA1 hash if present
        line = line.split("|")[0]

        # Get the file path
        file_path = line.split(";")[0].split(":")[-1]
        if file_path[0] == "-":
            file_path = file_path[1:]

        try:
            with open(os.path.join(self.vendor_path, file_path), "rb") as f:
                hash_value = sha1(f.read()).hexdigest()
            return f"{line}|{hash_value}", need_sha1
        except FileNotFoundError:
            print(f"Warning: File not found: {file_path}")
            return line, need_sha1
        except IOError as e:
            print(f"Warning: Error reading {file_path}: {e}")
            return line, need_sha1

    def cleanup(self) -> None:
        """Remove all SHA1 hashes from the file."""
        for index, line in enumerate(self.lines):
            # Skip empty or commented lines
            if not line or line[0] == "#" or "|" not in line:
                continue
            # Drop SHA1 hash
            self.lines[index] = line.split("|")[0]

    def update(self) -> None:
        """Update SHA1 hashes for all files."""
        need_sha1 = False
        for index, line in enumerate(self.lines):
            self.lines[index], need_sha1 = self.process_line(line, need_sha1)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update or clean SHA1 hashes in proprietary-files.txt"
    )
    parser.add_argument(
        "-c", "--cleanup", action="store_true", help="Remove all SHA1 hashes"
    )
    parser.add_argument(
        "--device", default="garnet", help="Device name (default: garnet)"
    )
    parser.add_argument(
        "--vendor", default="xiaomi", help="Vendor name (default: xiaomi)"
    )
    parser.add_argument(
        "--file",
        default="proprietary-files.txt",
        help="Proprietary files list (default: proprietary-files.txt)",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    updater = SHA1Updater(args.device, args.vendor, args.file)
    updater.read_proprietary_files()

    if args.cleanup:
        updater.cleanup()
    else:
        updater.update()

    updater.write_proprietary_files()


if __name__ == "__main__":
    main()
