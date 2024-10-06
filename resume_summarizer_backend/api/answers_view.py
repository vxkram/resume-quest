import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class SaveAnswersView(APIView):
    def post(self, request, file_name, *args, **kwargs):
        json_file_path = os.path.join('saved_jsons', f"{file_name}.json")
        

        if not os.path.exists(json_file_path):
            return Response({"error": "JSON file not found."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Load the JSON file
            with open(json_file_path, 'r') as json_file:
                data = json.load(json_file)


            data['user_answers']['answers_to_questions'] = request.data.get('answers', [])


            with open(json_file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)

            return Response({"message": "Answers saved successfully."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
