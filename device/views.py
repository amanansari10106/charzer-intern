# from functools import partial
# from django.http import response
from rest_framework.fields import MISSING_ERROR_MESSAGE
from device.models import device, dustbin, washroom, waterpoint
from agent.models import agent
# from django.shortcuts import render
# first lat then long
from django.http import HttpResponse, response
import math
from rest_framework.views import APIView
from agent.models import agent
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from device.serializers import deviceserializer, dustbinserializer, washroomserializer, waterpointserializer, updatedeviceserializer, updatedustbinserializer, updatewashroomserializer, updatewaterpointserializer
# Create your views here.
from math import acos, sin, cos
class deviceapi(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes  = [IsAuthenticated]

    def get(self, request):
        try :
            ndevice = device.objects.get(device_id = request.data["device_id"])
            ser = deviceserializer(ndevice)
            dat = ser.data
            if ndevice.device_type == "dustbin":
                ndustbin = dustbin.objects.get(device=ndevice)
                dustserializer = dustbinserializer(ndustbin)
                dat.update(dustserializer.data)
            elif ndevice.device_type == "waterpoint":
                nwaterpoint = waterpoint.objects.get(device=ndevice)
                waterserializer =waterpointserializer(nwaterpoint)
                dat.update(waterserializer.data)

            return Response(dat, status=status.HTTP_200_OK)

        except Exception as e:
            msg = {
                "resp":"fail",
                "msg": f"{e}"
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try :
            data = request.data
            device_mac = data["device_mac"]
            if device.objects.filter(device_mac=device_mac).exists():
                return Response({"resp":"fail", "msg":"device already connected to another agent"})
            else:
                nagent = agent.objects.get(user = request.user)
                device_lat = data["device_lat"]
                device_long = data["device_long"]
                device_type = data["device_type"]
                ndevice = device(agent=nagent, device_lat=device_lat, device_long=device_long, device_type=device_type, device_mac=device_mac)
                ndevice.save()
                if device_type == "dustbin":
                    z = dustbin(device = ndevice, dustbin_level=data["dustbin_level"])
                    z.save()
                    ds = dustbinserializer(z)
                    dat = ds.data
                elif device_type == "waterpoint":
                    z = waterpoint(device=device, water_level=data["water_level"])
                    z.save()
                    ws = waterpointserializer(z)
                    dat = ws.data
                
                else:
                    msg = {
                        "resp":"fail",
                        "msg":"invalid device type"
                    }
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)
                s = deviceserializer(ndevice)
                dat.update(s.data)
                return Response(dat, status=status.HTTP_200_OK)
            
            

        except Exception as e:
            msg ={
                "resp":"fail",
                "msg": f"{e}"
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):

        try :
            nagent = agent.objects.get(user=request.user)
            ndevice = device.objects.get(device_id=request.data["device_id"])
            if ndevice.agent == nagent:
                devserializer = updatedeviceserializer(ndevice, data=request.data, partial=True)
                if devserializer.is_valid():
                    devserializer.save()
                    ndevice = device.objects.get(device_id=request.data["device_id"])
                    devserializer = deviceserializer(ndevice)
                    dat = devserializer.data
                else:
                    msg = {
                        "resp":"fail",
                        "msg":f"{devserializer.errors}"
                    }
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)
                if ndevice.device_type == "dustbin":
                    ndustbin = dustbin.objects.get(device=ndevice)
                    dustserializer = updatedustbinserializer(ndustbin, data=request.data, partial=True)
                    if dustserializer.is_valid():
                        dustserializer.save()
                        ndustbin = dustbin.objects.get(device=ndevice)
                        dustserializer = dustbinserializer(ndustbin)
                        dat.update(dustserializer.data)
                    else:
                        msg = {
                        "resp":"fail",
                        "msg":f"{dustserializer.errors}"
                        }
                        return Response(msg, status=status.HTTP_400_BAD_REQUEST)
                    
                elif ndevice.device_type == "waterpoint":
                    nwaterpoint = waterpoint.objects.get(device=ndevice)
                    waterserializer = updatewaterpointserializer(nwaterpoint, data=request.data, partial=True)
                    if waterserializer.is_valid():
                        waterserializer.save()
                        nwaterpoint = waterpoint.objects.get(device=ndevice)
                        waterserializer = waterpointserializer(nwaterpoint)
                        dat.update(waterserializer.data)
                    else:
                        msg = {
                        "resp":"fail",
                        "msg":f"{waterserializer.errors}"
                        }
                        return Response(msg, status=status.HTTP_400_BAD_REQUEST)
                
                return Response(dat, status=status.HTTP_200_OK)

           
        except Exception as e:
            return Response({"errorf":f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


class near(APIView):
    def get(self, request):
        try :
            print(request.objects)
            lat = request.data["user_lat"]
            lon = request.data["user_long"]
            lat = math.radians(float(lat))
            lon = math.radians(float(lon))
            range = int(request.data["range"]) + 10
            near_device_obj = device.objects.raw(f'SELECT device_id, 6371.01 * acos(sin({lat})*sin(radians(device_lat)) + cos({lat})*cos(radians(device_lat))*cos({lon} - radians(device_long))) AS distance FROM DEVICE_DEVICE GROUP BY device_id HAVING distance < {range}')
            # near_device_obj = device.objects.raw(f'SELECT device_id, ROUND (6371.01 * acos(sin({lat})*sin(radians(device_lat)) + cos({lat})*cos(radians(device_lat))*cos({lon} - radians(device_long)))) AS distance FROM DEVICE_DEVICE GROUP BY device_id HAVING distance <11')
            ser = deviceserializer(near_device_obj, many=True)
            # dist = 6371.01 * acos(sin(slat)*sin(elat) + cos(slat)*cos(elat)*cos(slon - elon))
            msg = {
                "resp": "success",
                "device_list" : ser.data
            }
            return Response(msg, status= status.HTTP_200_OK)
        except Exception as e:
            msg = {
                "resp":"fail",
                "msg":f"{e}"
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)



# lat = 4554.454
# lon = 456.56
# elat = 
# elon = lon

def test(request):
    # lat = 0.38761956271018244
    # lon = 1.420312014106013
    # elat = 0.38761956271018244
    # elon = 1.420312014106013
    lat = math.radians(21.208966)
    lon = math.radians(81.377884)
    elat = math.radians(21.208966)
    elon = math.radians(81.377884)
    # re = device.objects.raw('SELECT device_id, ( 3959 * acos( cos( radians(device_lat) ) * cos( radians( device_lat ) ) * cos( radians( device_long ) - radians(-device_long) ) + sin( radians(37) ) * sin( radians( device_lat ) ) ) ) AS distance FROM DEVICE_DEVICE GROUP BY device_id HAVING distance < 25 ORDER BY distance LIMIT 0 , 20;')
    # re = device.objects.raw(f'SELECT device_id, abs(( 3959 * acos( cos( radians({lat}) ) * cos( radians( device_lat ) ) * cos( radians( device_long ) - radians({long}) ) + sin( radians({lat}) ) * sin( radians( device_lat ) ) ) ) ) AS distance FROM DEVICE_DEVICE GROUP BY device_id HAVING distance > 1 ORDER BY distance LIMIT 0 , 20;')
    # re = device.objects.raw('SELECT device_id, ( 3959 * acos( cos( radians(37) ) * cos( radians( device_lat ) ) * cos( radians( device_long ) - radians(-122) ) + sin( radians(37) ) * sin( radians( device_lat ) ) ) ) AS distance FROM DEVICE_DEVICE GROUP BY device_id HAVING distance < 25 ORDER BY distance LIMIT 0 , 20;')
    # re = device.objects.raw(f'SELECT device_id, 6371.01 * acos(sin({lat})*sin(elat) + cos({lat})*cos(elat)*cos({long} - elon))')
    t = 6371.01 * acos(sin(lat)*sin(elat) + cos(lat)*cos(elat)*cos(lon - elon))
    # re = device.objects.raw(f'SELECT device_id, ( 3959 * acos( cos( radians({lat}) ) * cos( radians( device_lat ) ) * cos( radians( device_long ) - radians({lon}) ) + sin( radians({lat}) ) * sin( radians( device_lat ) ) ) ) AS distance FROM DEVICE_DEVICE GROUP BY device_id HAVING distance < 100')
    # f = 
    print(t)

    # near_device_obj = device.objects.raw(f'SELECT device_id, 6371.01 * acos(sin({lat})*sin(device_lat) + cos({lat})*cos(device_lat)*cos({lon} - device_long)) AS distance FROM DEVICE_DEVICE GROUP BY device_id HAVING distance >200')
    return HttpResponse(t)