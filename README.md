# DemoEplusAPI
Django + EPlusAPI w00t!

# Setup
- Clone the repo: `git clone https://github.com/Myoldmoapr/DemoEplusAPI`
- Set up a Python environment `python3 -m venv blahJustLetPyCharmDoIt`
- Install dependencies: `pip install -r requirements.txt`

# Running with Django Server
- Run the server: `python3 manage.py runserver`
- Open the webpage: `xdg-open http://127.0.0.1:8000`
- Modify the `plot_e_plus.py` script to point to a build of EnergyPlus supporting the API along with paths to EPW, etc.
- Also set `get_by_api` to `False` in that script for a quick test
- Run the `plot_e_plus.py` script, it should run quickly and plot the E+ results with the weather file
- Modify the `plot_e_plus.py` script with `get_by_api = True` so that the script will try to interact with the server
- Run the `plot_e_plus.py` script, it should run much slower since it is making thousands of API calls into the server
  - While it is running use the spinbox in the browser to vary the outdoor temperature, crazy right!
  
# Running with CLI User Input
- Run the `plot_e_plus_with_cli_user_input.py` script
- Enter the user inputs for temperature when requested.
  - `Enter a new outdoor air temperature <int or float>:`