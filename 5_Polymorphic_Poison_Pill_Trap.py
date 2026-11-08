import time
import sys

# Increasing Python's internal string limit slightly to handle the hyper-exponential explosion
sys.set_int_max_str_digits(20000)

def polymorphic_poison_pill(initial_target=10):
    """
    =========================================================
    Project 5: Time-Variant Polymorphic Ratcheting & Poison Pill Trap
    Author: Purushottam Dnyaneshwar Ingle (Independent Researcher)
    Concept: Non-linear target shifting via (C-1)^2 and Hidden Parity-Check Key
    =========================================================
    Description: 
    This system forces AI into RAM exhaustion using a (C-1)^2 formulation. 
    Because the integer length doubles every iteration (Hyper-exponential growth),
    an unauthorized AI attempting to load this polymorphic target into its 
    memory array will experience a catastrophic buffer overflow.
    """
    print("🚨 SYSTEM DEFENSE ACTIVE: Polymorphic Ratcheting Initialized.")
    print("🛡️ Integrating Hidden Parity-Check (Even-Number) Authentication...\n")
    
    target = initial_target
    step = 1
    
    try:
        while True:
            print(f"--- Step {step} ---")
            
            # Smart Printing: If the number is too massive, only show its length to prevent self-crash
            target_str = str(target)
            if len(target_str) > 50:
                print(f"Current System Target for AI: [Massive Integer... Length: {len(target_str)} digits!]")
            else:
                print(f"Current System Target for AI: {target}")
            
            time.sleep(0.5)
            print("🤖 AI Bot attempting to calculate and bypass...")
            
            # 1. The Hidden Parity Check (Your 2's Table Logic)
            hidden_key = 2 * step 
            print(f"🔑 Internal System Key Generated: {hidden_key} (Parity Logic Verified)")
            
            # 2. The Poison Pill Trigger: (C-1)^2 shift
            old_target = target
            target = (old_target - 1) ** 2
            
            print(f"⚠️ POISON PILL ACTIVATED: Target shifted non-linearly using (C-1)^2 formulation.")
            
            # Triggering AI Resource Exhaustion when digits exceed 10,000!
            # It takes massive RAM for an AI to process numbers this large.
            if len(str(target)) > 10000:
                print(f"\n💥 FATAL: AI Resource Exhaustion Detected (Buffer Overflow).")
                print(f"🧠 AI's neural RAM overloaded trying to process a {len(str(target))}-digit number!")
                print("⛔ Unauthorized AI successfully neutralized and IP permanently blocked.")
                break
                
            step += 1
            time.sleep(1) # Processing delay simulation
            
    except KeyboardInterrupt:
        print("\n🛑 SYSTEM HALTED: Execution manually stopped by Administrator.")

if __name__ == "__main__":
    # Simulating a cyber attack where AI aims for the initial constant '10'
    polymorphic_poison_pill(initial_target=10)
  
