from json import loads
from os import makedirs, path
from platform import system
from shutil import rmtree
import sys
from time import sleep
from threading import Thread

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


class RunConfig:
    Install = 1
    Build = 2
    Current = Install


class FileToRun:
    OneZoneUncontrolled = 1
    FiveZoneAirCooled = 2
    Current = OneZoneUncontrolled


if RunConfig.Current == RunConfig.Install:
    IDFDir = 'ExampleFiles'
    EPWDir = 'WeatherData'
else:  # Assume Build
    IDFDir = 'testfiles'
    EPWDir = 'weather'

if system() == 'Linux':
    if RunConfig.Current == RunConfig.Install:
        ProductsDir = '/eplus/installs/EnergyPlus-9-5-0'
        RepoRoot = '/eplus/installs/EnergyPlus-9-5-0'
    else:  # Assume Build
        ProductsDir = '/eplus/repos/1eplus/builds/r/Products'
        RepoRoot = '/eplus/repos/1eplus'
elif system() == 'Darwin':
    if RunConfig.Current == RunConfig.Install:
        ProductsDir = '/Applications/EnergyPlus-9-5-0'
        RepoRoot = '/Applications/EnergyPlus-9-5-0'
    else:  # Assume Build
        ProductsDir = '/Users/elee/eplus/repos/1eplus/builds/r/Products'
        RepoRoot = '/Users/elee/eplus/repos/1eplus'
else:  # Assume Windows
    if RunConfig.Current == RunConfig.Install:
        ProductsDir = 'C:/EnergyPlus-9-5-0'
        RepoRoot = 'C:/EnergyPlus-9-5-0'
    else:  # Assume Build
        ProductsDir = 'C:/EnergyPlus/repos/1eplus/builds/VS64/Products/Release'
        RepoRoot = 'C:/EnergyPlus/repos/1eplus'

if FileToRun.Current == FileToRun.OneZoneUncontrolled:
    TestFileName = '1ZoneUncontrolled.idf'
    ZoneName = 'Zone One'
else:  # Assume 5ZoneAirCooled
    TestFileName = '5ZoneAirCooled.idf'
    ZoneName = 'Space1-1'


# Here are the living variables that we will use in the server
eplus_outdoor_temp = 23.3
eplus_output = b"(No Output Yet)"
eplus_progress = 0
got_handles = False
oa_temp_actuator = -1
oa_temp_handle = -1
zone_temp_handle = -1
api = None
count = 0
outdoor_data = []
zone_temp_data = []


@csrf_exempt
def get_data(request):
    if request.method == 'GET':
        return JsonResponse(
            {
                "output": eplus_output.decode('utf-8'),
                "progress": eplus_progress + 1,
                "outdoor_data": outdoor_data,
                "zone_temp_data": zone_temp_data
            }
        )
    else:
        return JsonResponse({"message": "Can only GET or POST with this endpoint"}, status=400)


def eplus_output_handler(msg):
    global eplus_output
    eplus_output += msg + b'\n'


def eplus_progress_handler(p):
    global eplus_progress
    eplus_progress = p


def callback_function(s):
    global count, got_handles, oa_temp_actuator, oa_temp_handle, zone_temp_handle, zone_temp_data
    if not got_handles:
        if not api.exchange.api_data_fully_ready(s):
            return
        oa_temp_actuator = api.exchange.get_actuator_handle(s, "Weather Data", "Outdoor Dry Bulb", "Environment")
        oa_temp_handle = api.exchange.get_variable_handle(s, "Site Outdoor Air DryBulb Temperature", "Environment")
        zone_temp_handle = api.exchange.get_variable_handle(s, "Zone Mean Air Temperature", ZoneName)
        if -1 in [oa_temp_actuator, oa_temp_handle, zone_temp_handle]:
            print("***Invalid handles, check spelling and sensor/actuator availability")
            sys.exit(1)
        got_handles = True
    if api.exchange.warmup_flag(s):
        return
    count += 1
    sleep(0.0002)
    if count % 200 != 0:
        return
    api.exchange.set_actuator_value(s, oa_temp_actuator, eplus_outdoor_temp)
    oa_temp = api.exchange.get_variable_value(s, oa_temp_handle)
    outdoor_data.append({'x': count, 'y': oa_temp})
    zone_temp = api.exchange.get_variable_value(s, zone_temp_handle)
    zone_temp_data.append({'x': count, 'y': zone_temp})


def thread_function():
    global api, eplus_output, eplus_progress, count, outdoor_data, zone_temp_data
    eplus_output = b""
    eplus_progress = 0
    count = 0
    outdoor_data = []
    zone_temp_data = []
    sys.path.insert(0, str(ProductsDir))  # don't do this every time
    from pyenergyplus.api import EnergyPlusAPI
    working_dir = f"/tmp/test_thread_1"
    if path.exists(working_dir):
        rmtree(working_dir)
    makedirs(working_dir)
    api = EnergyPlusAPI()
    state = api.state_manager.new_state()
    api.exchange.request_variable(state, "Site Outdoor Air DryBulb Temperature", "Environment")
    api.exchange.request_variable(state, "Zone Mean Air Temperature", ZoneName)
    api.runtime.callback_begin_zone_timestep_after_init_heat_balance(state, callback_function)
    api.runtime.callback_message(state, eplus_output_handler)
    api.runtime.callback_progress(state, eplus_progress_handler)
    api.runtime.run_energyplus(
        state, [
            '-d',
            working_dir,
            '-a',
            '-w',
            path.join(RepoRoot, EPWDir, 'ChicagoNoSolar.epw'),  # 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'),
            path.join(RepoRoot, IDFDir, TestFileName)
        ]
    )


@csrf_exempt
def start(request):
    if request.method == 'GET':
        ...
    elif request.method == 'POST':
        Thread(target=thread_function).start()
    else:
        return JsonResponse({"message": "Can only GET or POST with this endpoint"}, status=400)
    return JsonResponse({})


@csrf_exempt
def outdoor_temp(request):
    global eplus_outdoor_temp
    if request.method == 'GET':
        ...
    elif request.method == 'POST':
        data = loads(request.body)
        if 'temperature' not in data:
            return JsonResponse({"message": "Need to supply 'temperature' in POST data as a float"}, status=400)
        temp = float(data['temperature'])
        eplus_outdoor_temp = temp
    else:
        return JsonResponse({"message": "Can only GET or POST with this endpoint"}, status=400)
    return JsonResponse({"outdoor_temp": eplus_outdoor_temp})


def home(request):
    return render(request, 'index.html')
