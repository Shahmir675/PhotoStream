import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile
from app.config import settings
from typing import Dict
import io

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret
)


class CloudinaryService:
    def __init__(self):
        self.folder = "photostream"
        self.profile_folder = "photostream/profiles"

    async def upload_image(self, file: UploadFile) -> Dict[str, str]:
        """Upload image to Cloudinary"""
        try:
            # Read file content
            contents = await file.read()

            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                contents,
                folder=self.folder,
                resource_type="image",
                format="jpg",
                transformation=[
                    {'quality': "auto:good"},
                    {'fetch_format': "auto"}
                ]
            )

            # Generate thumbnail URL
            thumbnail_url = cloudinary.CloudinaryImage(result['public_id']).build_url(
                width=300,
                height=300,
                crop="fill",
                quality="auto:low"
            )

            return {
                "public_id": result['public_id'],
                "url": result['secure_url'],
                "thumbnail_url": thumbnail_url,
                "width": result.get('width'),
                "height": result.get('height'),
                "format": result.get('format'),
                "size": result.get('bytes')
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload image: {str(e)}"
            )
        finally:
            # Reset file pointer
            await file.seek(0)

    async def delete_image(self, public_id: str) -> bool:
        """Delete image from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete image: {str(e)}"
            )

    async def upload_profile_picture(self, file: UploadFile, user_id: str) -> Dict[str, str]:
        """Upload profile picture to Cloudinary"""
        try:
            # Read file content
            contents = await file.read()

            # Upload to Cloudinary with specific transformations for profile pictures
            result = cloudinary.uploader.upload(
                contents,
                folder=self.profile_folder,
                public_id=f"user_{user_id}",
                overwrite=True,  # Replace existing profile picture
                resource_type="image",
                format="jpg",
                transformation=[
                    {'width': 400, 'height': 400, 'crop': "fill", 'gravity': "face"},
                    {'quality': "auto:good"},
                    {'fetch_format': "auto"}
                ]
            )

            return {
                "public_id": result['public_id'],
                "url": result['secure_url']
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload profile picture: {str(e)}"
            )
        finally:
            # Reset file pointer
            await file.seek(0)
