# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from bbq_thermometer.models import Session, Datum
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
    filter_fields = ('session',)


    # def create(self, request, *args, **kwargs):
    #     try:
    #         if request.data.get('session', None) is None:
    #             try:
    #                 request.data['session'] = Session.objects.get(date=datetime.date.today()).id
    #             except (IntegrityError, Session.DoesNotExist):
    #                 session = Session.objects.create()
    #                 request.data['session'] = session.id
    #         server_response = super(ReadViewSet, self).create(request, *args, **kwargs)
    #         return server_response
    #     except Exception as e:
    #         print e, type(e)
    #         return response.Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)


class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        # FIXME - IMPLEMENT INTERNAL AND EXTERNAL TEMPERATURE FILTERS
        request_params = request.query_params
        session = request_params.get('session', None)
        sessions = Session.objects.all()
        response = {'data': {'datasets': []}}

        if sessions:
            if session is None or session == '':
                session = Session.objects.all().order_by('-start_date')[0].id
            data = Datum.objects.filter(session__id=session).order_by('timestamp')

            probes = set(data.values_list('probe', flat=True))

            for idx, probe in enumerate(list(probes)):
                response['data']['datasets'].append({'data': [], 'label': "Probe {}".format(probe)})
                temp_data = []
                for datum in data.filter(probe=probe):
                    temp_data.append(
                        {"x": int(datum.timestamp.strftime("%s")) * 1000,
                         "y": datum.value}
                    )

                response['data']['datasets'][idx]['data'] = temp_data

        return Response(response)


class ChartView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        return render(request, "chart.html", {})
