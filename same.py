import random

number = random.randint(1, 100)
print("Your random number is:", number)

import random
import string
import time

# Random number generator
def random_number(min_val=1, max_val=100):
    return random.randint(min_val, max_val)

# Random word generator
def random_word(length=5):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

# Random sentence generator
def random_sentence(words=6):
    sentence = ' '.join(random_word(random.randint(3, 8)) for _ in range(words))
    return sentence.capitalize() + '.'

# Random lottery game
def lottery_game():
    print("Welcome to the Random Lottery!")
    user_numbers = [random_number(1, 50) for _ in range(5)]
    winning_numbers = [random_number(1, 50) for _ in range(5)]
    print("Your numbers:", user_numbers)
    print("Winning numbers:", winning_numbers)
    matches = len(set(user_numbers) & set(winning_numbers))
    print(f"You matched {matches} number(s)!")
    if matches >= 3:
        print("Congratulations, you won!")
    else:
        print("Better luck next time!")

# Main random generator loop
def main():
    print("=== RANDOM GENERATOR SCRIPT ===")
    for i in range(3):
        print(f"\nRandom Number {i+1}: {random_number()}")
        print(f"Random Word {i+1}: {random_word(random.randint(4, 10))}")
        print(f"Random Sentence {i+1}: {random_sentence(random.randint(4, 10))}")
        time.sleep(1)

    print("\nNow let's play a quick lottery!")
    lottery_game()

if __name__ == "__main__":
    main()