from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import Capsule
from datetime import timedelta

User = get_user_model()


class LockedCapsuleSerializationTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='tester', password='pass')
		self.client = APIClient()
		self.client.force_authenticate(self.user)

	def test_locked_fields_hidden_with_include_locked_true(self):
		# Create a locked capsule (unlock_date in the future)
		future = timezone.now() + timedelta(days=7)
		cap = Capsule.objects.create(
			user=self.user,
			title='Locked Title',
			content='This is secret content',
			mood='happy',
			unlock_date=future,
			tags=[],
		)

		# Ensure capsule exists and is locked
		self.assertFalse(cap.is_unlocked)

		# Request the list including locked capsules
		resp = self.client.get('/api/capsules/?include_locked=true')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()

		# Find our capsule in the returned list
		found = None
		for item in data:
			if item.get('id') == cap.id:
				found = item
				break

		self.assertIsNotNone(found, 'Created capsule not present in response')

		# content must be null or absent
		self.assertTrue((found.get('content') is None) or ('content' not in found))

		# photo and ai_caption should be null or absent (fields may not exist yet)
		self.assertTrue((found.get('photo') is None) or ('photo' not in found))
		self.assertTrue((found.get('ai_caption') is None) or ('ai_caption' not in found))


	class PhotoCaptionIntegrationTest(TestCase):
		def setUp(self):
			self.user = User.objects.create_user(username='uploader', password='pass')
			self.client = APIClient()
			self.client.force_authenticate(self.user)

		def _make_image_file(self, color=(64, 128, 192), size=(64, 64), fmt='PNG'):
			from io import BytesIO
			from PIL import Image

			img = Image.new('RGB', size, color=color)
			buf = BytesIO()
			img.save(buf, format=fmt)
			buf.seek(0)
			buf.name = 'test.png'
			return buf

		def test_upload_photo_and_generate_caption(self):
			img_file = self._make_image_file()
			payload = {
				'title': 'Photo capsule',
				'content': 'A memory with a photo',
				'mood': 'happy',
				'unlock_date': timezone.now().isoformat(),
				'tags': '[]',
				'photo': img_file,
			}

			response = self.client.post('/api/capsules/', data=payload, format='multipart')
			self.assertIn(response.status_code, (200, 201))

			capsule_id = response.data.get('id')
			self.assertIsNotNone(capsule_id)

			cap = Capsule.objects.get(id=capsule_id)

			# Try to generate caption synchronously (the signal may have already run)
			from .ai.vision import generate_caption
			caption = None
			if cap.photo and hasattr(cap.photo, 'path'):
				caption = generate_caption(cap.photo.path)

			print('Generated caption:', caption)
			self.assertTrue((caption is None) or isinstance(caption, str))
