from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import MarackerApplicationSerializer
from .serializers import DockerContainerSerializer, MarathonConfigSerializer
from .models import MarackerApplication, DockerContainer, MarathonConfig
from .services import MarathonService
from django.conf import settings
from django.shortcuts import get_object_or_404


class ApplicationCreateView(generics.ListCreateAPIView):
    """
    get:
        Return all applications.


    post:
        Create a new application.
    """
    queryset = MarackerApplication.objects.all()
    serializer_class = MarackerApplicationSerializer

    def perform_create(self, serializer):
        serializer.save()


class ApplicationDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """
    get:
        Return an application instance.


    put:
        Update an application.


    patch:
        Update one or more field on an existing application.


    delete:
        Delete an existing application.
    """
    queryset = MarackerApplication.objects.all()
    serializer_class = MarackerApplicationSerializer

    def perform_destroy(self, instance):
        if instance.docker_container:
            instance.docker_container.delete()
        if instance.marathonconfig_set:
            instance.marathonconfig_set.all().delete()

        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ApplicationSlugView(generics.RetrieveUpdateDestroyAPIView):
    """
    get:
        Return an application instance.


    put:
        Update an application.


    patch:
        Update one or more field on an existing application.


    delete:
        Delete an existing application.
    """

    queryset = MarackerApplication.objects.all()
    serializer_class = MarackerApplicationSerializer
    lookup_field = "name"


class DockerDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """
    get:
        Return a Docker container instance.


    put:
        Update a Docker container.


    patch:
        Update one or more field on an existing Docker container.


    delete:
        Delete an existing Docker container.
    """
    queryset = DockerContainer.objects.all()
    serializer_class = DockerContainerSerializer


class MarathonDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """
    get:
        Return a Marathon configuration instance.


    put:
        Update a Marathon configuration.


    patch:
        Update one or more field on an existing Marathon configuration.


    delete:
        Delete an existing Marathon configuration.
    """
    queryset = MarathonConfig.objects.all()
    serializer_class = MarathonConfigSerializer


@api_view(['POST'])
def deploy(request, config_id):
    """
    post:
        Deploy an existing Marathon configuration.
    """
    config = get_object_or_404(MarathonConfig, pk=config_id)
    service = MarathonService(settings.MARATHON["URL"])
    service.deploy(config)
    serializer = MarathonConfigSerializer(config)
    return Response(serializer.data, status.HTTP_200_OK)


@api_view(['POST'])
def delete(request, config_id):
    """
    post:
        Remove an existing Marathon configuration from the Mesos cluster.
    """
    config = get_object_or_404(MarathonConfig, pk=config_id)
    service = MarathonService(settings.MARATHON["URL"])
    service.delete(config)
    serializer = MarathonConfigSerializer(config)
    return Response(serializer.data, status.HTTP_200_OK)
