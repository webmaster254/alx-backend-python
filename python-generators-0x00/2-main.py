#!/usr/bin/python3
"""
Test script for batch_processing function
"""
import sys
print("Importing batch_processing module...")
processing = __import__('1-batch_processing')
print("Successfully imported module.")

# Process users in a batch of 50 and print them out
try:
    print("Creating batch_processing generator...")
    # Create the generator
    users_gen = processing.batch_processing(50)
    print("Generator created successfully.")
    
    # Process and print users over 25
    print("\nUsers over 25 years old:")
    print("-" * 60)
    
    # Iterate through the generator to get users
    count = 0
    for user in users_gen:
        count += 1
        print(f"{count}. {user['name']} - {user['email']} (Age: {user['age']})")
        
        # Limit output to first 10 users for readability
        if count >= 10:
            print("\n... (showing only first 10 users) ...")
            # Continue iterating through the generator silently to exhaust it
            for _ in users_gen:
                pass
            break
    
    # Get summary statistics
    if hasattr(users_gen, 'gi_frame') and users_gen.gi_frame:
        summary = users_gen.gi_frame.f_locals
        print(f"\nProcessing summary:")
        print(f"- Total users processed: {summary.get('total_users', 0)}")
        print(f"- Users over 25: {summary.get('filtered_users', 0)}")
    else:
        print("\nGenerator exhausted, no summary statistics available.")
    
except BrokenPipeError:
    # Handle broken pipe errors gracefully
    sys.stderr.close()
    sys.exit(1)
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)