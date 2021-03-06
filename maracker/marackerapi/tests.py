from django.test import TestCase
from .services import get_docker_metadata, MarathonService
from .models import MarackerApplication, DockerContainer, MarathonConfig
from rest_framework.test import APIClient
from rest_framework import status
from django.core.urlresolvers import reverse
from django.conf import settings
import os


class MicrobadgerTestCase(TestCase):
    def setUp(self):
        pass

    def test_service_can_fetch_data_and_create_model(self):
        namespace, image_name = "hbpmip", "portal-backend"
        microbadger_data = get_docker_metadata(namespace, image_name)
        self.assertIsNotNone(microbadger_data)
        self.assertEqual(microbadger_data.image_name,
                         "/".join([namespace, image_name]))

    def test_service_handle_non_existent_image(self):
        microbadger_data = get_docker_metadata('toto', 'portal-backend')
        self.assertIsNone(microbadger_data)

    def test_service_handle_unexpected_values(self):
        microbadger_data = get_docker_metadata(None, None)
        self.assertIsNone(microbadger_data)


class MarathonServiceTestCase(TestCase):
    fixtures = ["marackerapi/fixtures/marackerapi.yaml"]

    def setUp(self):
        if os.getenv('TRAVIS', False):
            self.skipTest('skipped test as a Marathon instance is needed')
        self.service = MarathonService(settings.MARATHON["URL"])

    def test_marathon_service_can_create_and_delete_docker_app(self):
        app = MarackerApplication.objects.get(pk=1)
        marathon_conf = app.marathonconfig_set.first()

        deployed_app = self.service.deploy(marathon_conf)

        self.assertTrue(deployed_app)

        deployment = self.service.delete(marathon_conf)

        self.assertTrue(deployment)


class MarackerApplicationTestCase(TestCase):
    def setUp(self):
        pass

    def test_app_creation_and_marathon_conf_creation(self):
        before_count = MarackerApplication.objects.count()
        marackerapp = MarackerApplication(
            name="sleepy command",
            description="My first cmd app",
            command="sleep 7324")
        marackerapp.save()
        after_count = MarackerApplication.objects.count()
        self.assertNotEqual(before_count, after_count)
        before_count = MarathonConfig.objects.count()
        marathon_cmd = MarathonConfig(
            cpu=0.3, memory=128, maracker_app=marackerapp)
        marathon_cmd.save()
        after_count = MarathonConfig.objects.count()
        self.assertNotEqual(before_count, after_count)


class DockerContainerTestCase(TestCase):
    def setUp(self):
        pass

    def test_container_creation(self):
        container = DockerContainer(image="redis", ports=[80, 6359])

        before_count = DockerContainer.objects.count()
        container.save()
        after_count = DockerContainer.objects.count()
        self.assertNotEqual(before_count, after_count)

    def test_container_with_ports_creation(self):
        container = DockerContainer(image="redis", ports=[80, 6359])

        before_count = DockerContainer.objects.count()
        container.save()
        after_count = DockerContainer.objects.count()
        self.assertNotEqual(before_count, after_count)

    def test_marackerapp_container_relationship(self):
        marackerapp = MarackerApplication(
            name="postgres",
            description="Simple postgres container", )

        marackerapp.save()
        before_container = marackerapp.docker_container
        self.assertIsNone(before_container)

        container = DockerContainer(
            image="postgres", )

        before_count = DockerContainer.objects.count()
        container.save()
        after_count = DockerContainer.objects.count()
        self.assertNotEqual(before_count, after_count)

        marackerapp.docker_container = container
        marackerapp.save()
        app = MarackerApplication.objects.get(pk=marackerapp.id)
        after_container = app.docker_container
        self.assertIsNotNone(after_container)


class APIMarackerAppTestCase(TestCase):
    fixtures = ["marackerapi/fixtures/marackerapi.yaml"]

    def setUp(self):
        self.client = APIClient()

    def test_api_can_create_cmd_app(self):
        cmd_app = {
            "name": "my-cmd-app",
            "description": "be careful it's dangerous",
            "command": "env"
        }
        response = self.client.post(
            reverse("maracker.create"), cmd_app, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_api_can_create_app_with_container(self):
        # Without port exposure
        docker_app = {
            "name": "redis",
            "description": "Redis container",
            "docker_container": {
                "image": "library/redis",
            },
        }

        response = self.client.post(
            reverse("maracker.create"), docker_app, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # With port exposure
        docker_app = {
            "name": "redis",
            "description": "Redis container",
            "docker_container": {
                "image": "library/redis",
                "ports": [6539]
            },
        }

        # Check validation works
        response = self.client.post(
            reverse("maracker.create"), docker_app, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Post application needing port exposure
        docker_app["name"] = "redis-database"

        response = self.client.post(
            reverse("maracker.create"), docker_app, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_api_can_create_cmd_app_with_marathon_config(self):
        cmd_app = {
            "name":
            "hello-world",
            "command":
            "echo $MESSAGE",
            "marathon_configs": [{
                "env_vars": {
                    "MESSAGE": "Hello",
                }
            }, {
                "cpu": 0.1,
                "memory": 32,
                "env_vars": {
                    "MESSAGE": "Hola",
                }
            }]
        }
        response = self.client.post(
            reverse("maracker.create"), cmd_app, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cmd_app = MarackerApplication.objects.get(pk=response.data["id"])
        self.assertTrue(cmd_app.marathonconfig_set.all())

    def test_api_can_update_app(self):
        # Fetch the application to update
        app = MarackerApplication.objects.get(pk=1)

        before_configs = app.marathonconfig_set.count()
        before_container_image = app.docker_container.image

        response = self.client.get(
            reverse("maracker.details", kwargs={'pk': app.id}), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        app_data = response.data

        # Make some changes
        app_data["name"] = "redis"
        app_data["docker_container"] = {
            "image": "redis",
            "ports": [6379],
        }
        app_data["marathon_configs"].append({
            "cpus": 1.0,
            "memory": 256,
            "env_vars": {
                "hostname": "http://www.example.com",
            }
        })
        response = self.client.put(
            reverse("maracker.details", kwargs={'pk': app.id}),
            app_data,
            format="json")

        # Fetch the model again and validate new data
        app = MarackerApplication.objects.get(pk=1)
        after_configs = app.marathonconfig_set.count()
        after_container_image = app.docker_container.image

        self.assertTrue(before_configs < after_configs)
        self.assertIsNotNone(app.docker_container)
        self.assertNotEqual(before_container_image, after_container_image)

    def test_slug(self):
        response = self.client.get(
            reverse("maracker.details-slug", kwargs={"name": "database"}),
            format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        app_name = response.json()["name"]
        response = self.client.delete(
            reverse("maracker.details-slug", kwargs={"name": app_name}),
            format="json")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(
            reverse("maracker.details-slug", kwargs={"name": app_name}),
            format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
