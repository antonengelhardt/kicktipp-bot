# Kicktipp-Bot
This script can automatically enter tips into Kicktipp based on the quotes of the bookmakers. It is written in Python and uses Selenium to interact with the website.
## Installation

1. Clone the repository

2. Install chromedriver (https://chromedriver.chromium.org/downloads)

    Please choose the version that corresponds to your Chrome version.

3. Install the requirements
    
    ```pip3 install -r requirements.txt```

4. Set the constant `CHROMEDRIVER_PATH` to the path of the chromedriver executable.

    It is recommended to place the executable in the same directory as the script or into the Applications folder.

5. Set the constant `EMAIL` and `PASSWORD` at the top of the page

6. Execute the script