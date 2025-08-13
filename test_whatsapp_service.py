import unittest
from services.whatsapp_service import upload_media_to_whatsapp, create_whatsapp_template_with_media

class TestWhatsappService(unittest.TestCase):

    def test_upload_media_to_whatsapp(self):
        # Simulate a file upload and check if the handle is returned
        file_path = "test_image.jpg"  # Replace with a valid test file path
        file_type = "image/jpeg"
        result = upload_media_to_whatsapp(file_path, file_type)
        self.assertIsNotNone(result, "Media handle should not be None")

    def test_create_whatsapp_template_with_media(self):
        # Simulate template creation and check for success
        name = "test_template"
        content = "This is a test message"
        category = "UTILITY"
        media_handle = "2:c2FtcGxlLm1wNA==:image/jpeg:GKAj0gAUCZmJ1voFADip2iIAAAAAbugbAAAA:e:1472075513:ARZ_3ybzrQqEaluMUdI"  # Replace with a valid handle
        media_type = "IMAGE"
        language = "en_US"
        footer = "Test footer"

        result = create_whatsapp_template_with_media(name, content, category, media_handle, media_type, language, footer)
        self.assertIsNotNone(result, "Template creation should not return None")

if __name__ == "__main__":
    unittest.main()