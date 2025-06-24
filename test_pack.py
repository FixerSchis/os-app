#!/usr/bin/env python3
"""
Simple test script to debug pack serialization.
"""

import json
import os
import sys

from models.tools.pack import Pack

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_pack_serialization():
    """Test pack serialization to identify the issue."""

    # Test 1: Empty pack
    print("Test 1: Empty pack")
    pack1 = Pack()
    try:
        pack_dict = pack1.to_dict()
        json_str = json.dumps(pack_dict)
        print(f"Success: {json_str}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Pack with some data
    print("\nTest 2: Pack with data")
    pack2 = Pack(
        items=[1, 2, 3],
        exotics=[1],
        medicaments=[1],
        energy_chits=100,
        completion={"character_sheet": True, "character_id_badge": False},
    )
    try:
        pack_dict = pack2.to_dict()
        json_str = json.dumps(pack_dict)
        print(f"Success: {json_str}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 3: Pack with problematic completion data
    print("\nTest 3: Pack with problematic completion data")
    pack3 = Pack()
    pack3.completion = {"test": "not_boolean"}  # Non-boolean value
    try:
        pack_dict = pack3.to_dict()
        json_str = json.dumps(pack_dict)
        print(f"Success: {json_str}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 4: Pack with non-string keys
    print("\nTest 4: Pack with non-string keys")
    pack4 = Pack()
    pack4.completion = {123: True}  # Non-string key
    try:
        pack_dict = pack4.to_dict()
        json_str = json.dumps(pack_dict)
        print(f"Success: {json_str}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_pack_serialization()
