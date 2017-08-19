# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from bbq_thermometer.models import Session, Datum
from bbq_thermometer.utilities import convert_celsius_to_fahrenheit
from bbq_thermometer.serializers import DatumSerializer, SessionSerializer
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer

    #
    # def create(self, request, *args, **kwargs):
    #     # Overriding the create method
    #     try:
    #         return super(SessionViewSet, self).create(request, *args, **kwargs)
    #     except IntegrityError:
    #         # Found an existing model
    #         session = Session.objects.get(date=datetime.date.today())
    #         serializer = SessionSerializer(session)
    #         return response.Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class DatumViewSet(viewsets.ModelViewSet):
    queryset = Datum.objects.all()
    serializer_class = DatumSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ("session", "type")


    # def create(self, request, *args, **kwargs):
    #     try:
    #         if request.data.get("session", None) is None:
    #             try:
    #                 request.data["session"] = Session.objects.get(date=datetime.date.today()).id
    #             except (IntegrityError, Session.DoesNotExist):
    #                 session = Session.objects.create()
    #                 request.data["session"] = session.id
    #         server_response = super(ReadViewSet, self).create(request, *args, **kwargs)
    #         return server_response
    #     except Exception as e:
    #         print e, type(e)
    #         return response.Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)


class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        request_params = request.query_params
        session = request_params.get("session", None)
        datum_type = request_params.get("type", None)
        is_celsius = request_params.get("isCelsius", 'true') == 'true'  # Celsius or Fahrenheit flag
        sessions = Session.objects.all()

        # Allowing to filter by Data Type
        if datum_type is None or datum_type == "":
            datum_type = Datum.DATUM_CHOICES[0]
        else:
            datum_type = [choice for choice in Datum.DATUM_CHOICES if choice[0] == datum_type][0]

        response = {
            "chart": {
                "type": "line",
                "zoomType": "x",
            },
            "title": {
                "text": ""
            },
            "xAxis": {
                "type": "datetime"
            },
            "legend": {
                "enabled": True
            },
            "series": [],
            "responsive": {
                "rules": [{
                    "condition": {
                        "maxWidth": None
                    },
                    "chartOptions": {
                        "legend": {
                            "itemStyle": {
                                "fontSize": 20
                            },
                            "align": "center",
                            "verticalAlign": "bottom",
                            "layout": "horizontal"
                        },
                        "xAxis": [
                            {
                                "labels": {
                                    "style": {
                                        "fontSize": 14
                                    },
                                    "x": 0,
                                    "y": None
                                },
                            }
                        ],
                        "yAxis": [
                            {
                                "labels": {
                                "style": {
                                    "fontSize": 14
                                },
                                "align": "left",
                                "x": -15,
                                "y": -5
                                },
                                "title": {
                                    "style": {
                                        "fontSize": 18
                                    },
                                    "text": datum_type[1] if is_celsius else datum_type[1].replace("(°C)", "(F)"),
                                    "x": -10
                                }
                            }
                         ],
                        "subtitle": {
                            "text": None
                        },
                        "credits": {
                            "enabled": False
                        }
                    }
                }]
            }
        }

        if sessions:
            if session is None or session == "":
                session = Session.objects.all().order_by("-start_date")[0]
            else:
                session = Session.objects.get(id=session)

            response["title"]["text"] = "Session #{}: {}".format(session.id, session.start_date)
            data = Datum.objects.filter(session=session, type=datum_type[0]).order_by("timestamp")

            probes = set(data.values_list("probe", flat=True))

            for idx, probe in enumerate(list(probes)):
                response["series"].append(
                    {
                        "type": "line",
                        "data": [],
                        "name": u"{}".format(probe)
                    }
                )
                temp_data = []
                for datum in data.filter(probe=probe):
                    if is_celsius:
                        value = datum.value
                    else:
                        value = convert_celsius_to_fahrenheit(datum.value)
                    temp_data.append(
                        {"x": int(datum.timestamp.strftime("%s")) * 1000,  # Javascript timestamp
                         "y": value}
                    )

                response["series"][idx]["data"] = temp_data

        return Response(response)


class ChartView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        return render(request, "chart.html", {})
