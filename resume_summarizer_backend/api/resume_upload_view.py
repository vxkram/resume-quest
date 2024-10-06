import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.conf import settings
from gpt_integration.pdf_extractor import extract_text_from_pdf
from gpt_integration.openai_integration import generate_resume_summary_and_questions

class ResumeUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def get_unique_file_path(self, file_name, extension, base_directory):

        base_name = os.path.splitext(file_name)[0]  
        file_path = os.path.join(base_directory, f"{base_name}{extension}")
        counter = 1


        while os.path.exists(file_path):
            new_file_name = f"{base_name}_{counter}{extension}"
            file_path = os.path.join(base_directory, new_file_name)
            counter += 1

        return file_path

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')

        if file and file.content_type == 'application/pdf':
            try:
                
                pdf_directory = settings.MEDIA_ROOT
                json_directory = os.path.join(os.getcwd(), 'saved_jsons')

                
                os.makedirs(pdf_directory, exist_ok=True)
                os.makedirs(json_directory, exist_ok=True)

                
                pdf_file_path = self.get_unique_file_path(file.name, '.pdf', pdf_directory)

                
                with open(pdf_file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

                
                extracted_text = extract_text_from_pdf(pdf_file_path)

                
                base_file_name = os.path.splitext(os.path.basename(pdf_file_path))[0]
                json_file_path = self.get_unique_file_path(base_file_name, '.json', json_directory)

                
                openai_response = generate_resume_summary_and_questions(extracted_text, json_file_path)

                
                return Response(openai_response, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": f"Failed to upload file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": "Only PDF files are allowed."}, status=status.HTTP_400_BAD_REQUEST)
