from json import loads

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Here are the two living variables that we will use in the server
eplus_paused = False
eplus_outdoor_temp = 23.3


@csrf_exempt
def pause(request):
    global eplus_paused
    if request.method == 'GET':
        ...
    elif request.method == 'POST':
        data = loads(request.body)
        if 'state' not in data:
            return JsonResponse({"message": "Need to supply 'state' in POST data as true or false"}, status=400)
        this_state = bool(data['state'])
        eplus_paused = this_state
    else:
        return JsonResponse({"message": "Can only GET or POST with this endpoint"}, status=400)
    return JsonResponse({"pause": eplus_paused})


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
