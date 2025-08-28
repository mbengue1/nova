"""
interactive text mode for nova

this script allows you to interact with nova using text commands
without requiring voice input or wake word detection.
"""
import sys
import os

# add the project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import the brain directly
from core.brain import NovaBrain

def main():
    """run nova in interactive text mode"""
    print("\n=== nova interactive text mode ===")
    print("type your commands and press enter. type 'exit' to quit.\n")
    
    # initialize the brain
    brain = NovaBrain()
    
    # interactive loop
    while True:
        try:
            # get user input
            user_input = input("\n> you: ")
            
            # check for exit command
            if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                print("\nexiting nova interactive text mode. goodbye!")
                break
            
            # process the command
            response = brain.process_input(user_input)
            
            # display the response
            print(f"< nova: {response}")
            
        except KeyboardInterrupt:
            print("\n\nexiting nova interactive text mode. goodbye!")
            break
        except Exception as e:
            print(f"\nerror: {e}")
            print("please try again.")

if __name__ == "__main__":
    main()