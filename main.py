# wordle clone!

from sys import argv 
from random import choice as random_choice
# import rich for nice terminal text gameplay
from rich import print
from rich.text import Text, Span
from rich.style import Style
from rich.console import Console

console = Console(width=80)

# GLOBALS and game settings
TRIES_LIMIT = 6
WORD_LENGTH = 5 # can't be meaningfully changed without a new wordlist, but WILL break stuff!
WORDLIST_NAME = "Wordle Words.txt"
WORDLIST = []
LETTER_STATUS = {letter: Text(f" {letter} ") for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}


def load_wordlist() -> None:
    """
    Loads the wordlist found at WORDLIST_NAME into the WORDLIST global value.
    The wordlist file is expected to exist (in the current directory) and be non-empty.
    
    Only the first WORD_LENGTH letters are grabbed from each line of the wordlist: 
    if the wordlist is properly constructed for the chosen WORD_LENGTH then this will only remove newline characters.
    """

    try:
        with open(WORDLIST_NAME) as f:
            for line in f:
                # add each line from the file to wordlist
                # we assume the file contains words of the correct length, which lets us easily discard newline symbols
                # converting to uppercase to eliminate worries about case
                WORDLIST.append(line[0:WORD_LENGTH].upper())
    except FileNotFoundError:
        console.print(f" [red]Error:[/] Couldn't find wordlist \"{WORDLIST_NAME}\" in directory")
        exit(1)

    if len(WORDLIST) == 0:
        console.print(f" [red]Error:[/] Wordlist from \"{WORDLIST_NAME}\" is empty")
        exit(1)


def secret_word() -> str:
    """
    Returns a random word (uppercase) from the WORDLIST. 
    If the program received a commandline argument, then the word is set to that instead without restriction. 
    Note that, in favor of flexibility, this input is not validated, and can make the game unbeatable.
    """

    # checking for commandline arguments
    if len(argv) > 1:
        console.print(f"\n[yellow]Debug:[/] Secret word \"{argv[1].upper()}\" selected", justify="center")

        # warnings so player is aware if they chose an inconvenient word
        if len(argv[1]) != WORD_LENGTH:
            console.print(f"[cyan]Note:[/] Selected word isn't {WORD_LENGTH} letters long; game is unbeatable", justify="center")
        elif argv[1].upper() not in WORDLIST:
            console.print(f"[cyan]Note:[/] Selected word isn't in WORDLIST; game is unbeatable", justify="center")

        return argv[1].upper()

    # pick randomly from wordlist
    word = random_choice(WORDLIST)
    
    # converting to uppercase to eliminate worries about case
    return word.upper()


def game(wordle: str) -> bool:
    """
    Handles the rounds of the wordle game. Returns a bool indicating whether player won or lost.

    :param wordle: the secret WORD_LENGTH word that the player must guess
    """
    
    board = [Text("_____")] * TRIES_LIMIT # initialize the board with "empty" guesses
    tries = 0

    # welcome text
    console.print("") # spacing
    console.rule("[bold]WELCOME TO WORDLE![/]", characters="wordle_")
    console.print(f"\nI have picked a {WORD_LENGTH}-letter word, and you have {TRIES_LIMIT} rounds to guess it!\n", 
          "Type your guess and hit enter!\n", justify="center")

    # loop for a single round's logic
    while tries < TRIES_LIMIT:
        guess = read_input(tries)
        add_to_board(guess, wordle, board, tries)
        if guess == wordle: # has the word been guessed?
            return True
        tries += 1

    # player didn't guess the word in time = lose
    return False


def read_input(tries: int) -> str:
    """
    Reads input from the player and validates it. Returns the player's guess (uppercase).

    The validation criteria:
    - The guess must be WORD_LENGTH (default 5) letters long
    - The guess must be a word in the word list

    :param tries: The current round's number
    """

    not_valid = True
    while not_valid:
        guess = input(f" (round {tries+1} of {TRIES_LIMIT}): ")
        guess = guess.upper() # converting to uppercase to eliminate worries about case
        if len(guess) != WORD_LENGTH:
            print(f" Guess must be {WORD_LENGTH} letters!")
        elif guess not in WORDLIST:
            print(f" {guess} is not in wordlist!")
        else:
            not_valid = False
    return guess


def add_to_board(guess: str, wordle: str, board: list[Text], tries: int) -> None:
    """
    Colors and adds the new guess to the "board" with previous guesses, and reprints the board and status of the available letters to the terminal

    :param guess: The player's guess
    :param wordle: The secret word
    :param board: A list containing previous guesses, styled with Rich according to Wordle rules
    :param tries: The current round's number
    """

    pretty_guess = color_guess(guess, wordle)

    # add guess to board
    board[tries] = pretty_guess

    # print board
    for entry in board:
        console.print(entry, justify="center")
    console.print("") # spacing

    # print the statuses of the letters
    statuses = Text("").join(LETTER_STATUS.values())
    console.print(statuses, justify="center")
    console.print("") # spacing


def color_guess(guess: str, wordle: str) -> Text:
    """ 
    Styles the guess according to Wordle rules, returns the guess as a styled rich.Text object.

    :param guess: The player's guess
    :param wordle: The secret word

    ## The basic Wordle coloring rules:
    1. If a guessed letter is in the secret word in the correct position, color it green
    2. If a guessed letter is in the secret word, but not placed correctly, color it yellow
    3. If a guessed letter isn't in the secret word at all, don't color it (/ color it gray)

    ### Observations on the behaviour of duplicate letters:
    The game will only color the exact amount of the letters that appear in the secret word.
    Extra occurences of the letter in the guess are treated as if they don't appear in the word (uncolored)

    The game will prioritize coloring the letter green(!) above yellow, for example:
    - the secret word     STEPS
    - the guess           HEELS

    The game colors the second E green, even though the first occurence of E in HEELS would've been yellow

    Compare with:
    - the secret word     ELBOW
    - the guess           SLEEP

    Where the game colors the first E in SLEEP yellow
    """

    pretty_guess = Text(guess)

    # letter styles
    green_style = Style(color="black", bgcolor="green")
    yellow_style = Style(color="black", bgcolor="yellow")
    no_style = Style(color="black", bgcolor="#666666")

    ### now we color the letters:

    # to keep track of letter incidence we will detract 1 from the secret word's letter-frequency pairs for each match
    wordle_freq = letter_freq(wordle)

    # we prioritize coloring letters green
    for i in range(WORD_LENGTH):
        letter = guess[i]
        if letter == wordle[i] and wordle_freq[letter] > 0:
            pretty_guess.stylize(green_style, i, i+1)
            # color the status of the letter green too
            LETTER_STATUS[letter].stylize(green_style) # minor memory performance to be gained by checking whether letter already has a style, instead of just adding styles onto it
            wordle_freq[letter] -= 1

    # then we color the non-greens
    for i in range(WORD_LENGTH):
        # check that letter hasnt been colored green yet
        if Span(i, i+1, green_style) in pretty_guess.spans:
            continue

        # it hasnt, proceed with coloring yellow or gray
        letter = guess[i]
        if letter in wordle and wordle_freq[letter] > 0:
            pretty_guess.stylize(yellow_style, i, i+1)
            LETTER_STATUS[letter].stylize_before(yellow_style) # minor memory performance to be gained here too
            wordle_freq[letter] -= 1
        else:
            pretty_guess.stylize(no_style, i, i+1)
            LETTER_STATUS[letter].stylize_before(no_style) # minor memory performance to be gained here too

    return pretty_guess


def letter_freq(str: str) -> dict[str, int]:
    """Counts how many times each letter appears in input string. Returns dict containing letter-frequency pairs."""

    freqs = {}
    for letter in str:
        if letter in freqs.keys():
            freqs[letter] += 1
        else:
            freqs[letter] = 1
    return freqs


if __name__ == "__main__":
    load_wordlist()

    # pick secret word
    wordle = secret_word()

    # main loop of the game
    try:
        player_is_win = game(wordle)
    except KeyboardInterrupt:
        console.print("\nExiting game...", justify="center")
        exit(1)

    # win/lose logic
    if player_is_win:
        console.print(f"You did it! The word was [green]{wordle}[/]!", justify="center")
    else:
        console.print(f"Better luck next time! The word was [green]{wordle}[/]!", justify="center")