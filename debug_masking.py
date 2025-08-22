#!/usr/bin/env python3
"""Debug masking behavior"""

import asyncio
import sys
sys.path.insert(0, 'src')

from claude_litellm_proxy.proxy.integrated_masking import IntegratedMaskingSystem

async def debug_masking():
    masking = IntegratedMaskingSystem()
    
    # Clear all previous mappings
    await masking.clear_all_mappings()
    
    # Test individual items
    test_items = [
        "i-1234567890abcdef0",
        "i-abcdef1234567890a", 
        "vpc-12345678",
        "AKIA1234567890ABCDEF",
        "AKIA9876543210FEDCBA"
    ]
    
    print("Testing individual masking:")
    for item in test_items:
        masked, mappings = await masking.mask_text(item)
        print(f"{item} -> {masked} (mappings: {mappings})")
    
    print("\nTesting combined text:")
    combined = "EC2: i-1234567890abcdef0, i-abcdef1234567890a VPC: vpc-12345678"
    masked, mappings = await masking.mask_text(combined)
    print(f"Original: {combined}")
    print(f"Masked: {masked}")
    print(f"Mappings: {mappings}")
    
    print("\nTesting unmask:")
    unmasked = await masking.unmask_text(masked)
    print(f"Unmasked: {unmasked}")
    
    await masking.close()

if __name__ == "__main__":
    asyncio.run(debug_masking())