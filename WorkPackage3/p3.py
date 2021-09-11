import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
import time 
# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game
Score_Values = []   # Stores the scores fetched from the EEPROM using the fetch_scores function
totalscores = 0
scorecount = 0
value = 0
guess_num = 0
# DEFINE THE PINS USED HERE
LED_value = [11, 13, 15]
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
buzzer = 33
eeprom = ES2EEPROMUtils.ES2EEPROM()
buzzerpwm= None
ledpwm = None
# Print the game banner
def welcome():
    os.system('clear')
    print("  _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")


# Print the game menu
def menu():
    global end_of_game
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
    elif option == "P":
        os.system('clear')
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        value = generate_number()
        while not end_of_game:
            pass
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")


def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    print("There are {} scores. Here are the top 3!".format(count))
    # print out the scores in the required format

    counts = 1
    place = 0

    for data in raw_data:
        if place == 1:
            place += 1
        else :
            print("{} - {} took {} guesses".format(counts, data[0],data[1]))
            counts +=1
        if counts == 4:
            break
    pass


# Setup Pins
def setup():
    global LED_value, btn_submit, buzzer, btn_increase, LED_accuracy, ledpwm, buzzerpwm

    # Setup board mode
    GPIO.setmode(GPIO.BOARD)
    # Setup regular GPIO
    GPIO.setup(LED_value[0], GPIO.OUT)
    GPIO.setup(LED_value[1], GPIO.OUT)
    GPIO.setup(LED_value[2], GPIO.OUT)
    GPIO.setup(LED_accuracy, GPIO.OUT)
    GPIO.setup(buzzer, GPIO.OUT)

    # Configuring the pull up or pull down resistors:
    GPIO.setup(btn_increase, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(btn_submit, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Setup PWM channels
    ledpwm = GPIO.PWM(LED_accuracy, 50)
    buzzerpwm = GPIO.PWM(buzzer, 0.000000001)
    GPIO.output(buzzer, GPIO.LOW)
    
    #Setup all pins to low
    GPIO.setup(LED_value[0], GPIO.LOW)
    GPIO.setup(LED_value[1], GPIO.LOW)
    GPIO.setup(LED_value[2], GPIO.LOW)

    # Setup debouncing and callbacks
    GPIO.add_event_detect(btn_increase,GPIO.FALLING,callback= btn_increase_pressed,bouncetime=200)
    GPIO.add_event_detect(btn_submit,GPIO.FALLING,callback= btn_guess_pressed, bouncetime=200)
    
    pass

# Load high scores
def fetch_scores():
    # get however many scores there are
    score_count = eeprom.read_byte(0)

    # Form an array of scores and names taken from the EEPROM into a 2D array
    scorelist = []
    # Get the scores
    # convert the codes back to ascii
    for i in range(1, score_count+1):
        reset = []  #ensures that reset is emptied before every iteration
        score = eeprom.read_block(i,4) # This will read registers 1 to 4 from block i and place it into scores

        # Convert the "letter" registers into char values to generate words
        letter1 = chr(score[0])
        letter2 = chr(score[1])
        letter3 = chr(score[2])

        # Turn the letters into a word for the user name
        name = letter1 + letter2 + letter3
        # Adds the name formed and scores to an empty reset array as 2 entries
        reset.append(name)
        reset.append(score[3])

        scorelist.append(reset) #Adds the values from reset to scorelist, to form a 2D array of Name and Score
     # return back the results
    return score_count, scorelist


# Save high scores
def save_scores():
    global Score_Values, totalscores, scorecount
    # fetch scores
    totalscores,Score_Values = fetch_scores()
    eeprom.write_byte(0, totalscores+ 1)  # update total amount of scores
    Name = input("Enter a 3 letter name: \n")  # Prompt user for their Name
    inputScore = [Name[:3], scorecount] # Holder for the name and score number to be sent to the eeprom
    Score_Values.append(inputScore) #Adds the name and score counts to the score values array

    #sort
    sortedArray = sorted(Score_Values,key=lambda x: x[1])

    #Write the given values to the EEPROM
    transmittedvalues = []
    for Scores in sortedArray: #adds the name and score number to a matrix which is written into the eeprom
        for i in range(3): #loops through 3 letters in sortedArray and converts it into binary for the EEPROM
            transmittedvalues.append(ord(Scores[0][i]))
        transmittedvalues.append(Scores[1])
    eeprom.write_block(1,transmittedvalues)
    
    pass


# Generate guess number
def generate_number():
    return random.randint(0, pow(2, 3)-1)


# Increase button pressed
def btn_increase_pressed(channel):
    # Increase the value shown on the LEDs
    # You can choose to have a global variable store the user's current guess, 
    # or just pull the value off the LEDs when a user makes a guess
    global guess_num
    if guess_num == 8:
        guess_num = 0

    # Increase the value shown on the LEDs

    if GPIO.event_detected(channel):
        guess_num += 1

        GPIO.output(LED_value[0], guess_num & 0x01)
        GPIO.output(LED_value[1], guess_num & 0x02)
        GPIO.output(LED_value[2], guess_num & 0x04)
    pass

# Guess button
def btn_guess_pressed(channel):
    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    # Compare the actual value with the user value displayed on the LEDs
    # Change the PWM LED
    # if it's close enough, adjust the buzzer
    # if it's an exact guess:
    # - Disable LEDs and Buzzer
    # - tell the user and prompt them for a name
    # - fetch all the scores
    # - add the new score
    # - sort the scores
    # - Store the scores back to the EEPROM, being sure to update the score count
    global guess_num, scorecount, buzzer, value,buzzerpwm,ledpwm

    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    time_s = time.time()
    time_button = time.time() - time_s
    

    # Compare the actual value with the user value displayed on the LEDs
    while GPIO.input(channel) == 0:
        pass
    if time_button>2: 
        GPIO.cleanup()
        menu()
    # If they've guessed the wrong number update scoreCount and do a check on For Accuracy LED
    elif (guess_num!= value) :
        scorecount+=1
        accuracy_leds() 
        if (abs(value)-abs(guess_num)<=3):  
            trigger_buzzer()
    else:
        scorecount+=1 # Update scores
        GPIO.output(LED_value, False) # Switch off LEDs
        GPIO.output(buzzer,GPIO.LOW) # Switch off buzzer 
        save_scores() # The Above steps are done by save_scores
        menu() # return to menu
    pass
  

# LED Brightness
def accuracy_leds():
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
    global guess_num, ledpwm,value
    ledpwm.start(0)
    gn_1 = 8 - guess_num
    val_1 = 8 - value
    # Set the brightness of the LED based on how close the guess is to the answer
    if (guess_num < value):
        duty_cycle = (guess_num / value) * 100
        ledpwm.ChangeDutyCycle(duty_cycle)

    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
    else:
        duty_cycle_1 = (gn_1 / val_1) * 100
        ledpwm.ChangeDutyCycle(duty_cycle_1)
    pass

# Sound Buzzer
def trigger_buzzer():
    global guess_num, buzzerpwm, value
    # The buzzer operates differently from the LED
    # While we want the brightness of the LED to change(duty cycle), we want the frequency of the buzzer to change
    # The buzzer duty cycle should be left at 50%
    if abs(value - guess_num) >=3:
        buzzerpwm.start(50)
    elif abs(value-guess_num)==2:
        buzzerpwm.ChangeFrequency(2)
        buzzerpwm.start(50)
    elif abs(value-guess_num)==1:
        buzzerpwm.ChangeFrequency(4)
        buzzerpwm.start(50)
    pass
               

if __name__ == "__main__":
    try:
        # Call setup function
        setup()
        welcome()
        while True:
            menu()
            pass
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
