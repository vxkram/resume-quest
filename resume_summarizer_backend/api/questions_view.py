import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class QuestionsView(APIView):
    def get(self, request, file_name, *args, **kwargs):

        if not file_name.endswith('.json'):
            file_name += '.json'

        json_file_path = os.path.join('saved_jsons', file_name)

        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                data = json.load(json_file)
                questions = data.get("questions", [])
                return Response({"questions": questions}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Questions not found."}, status=status.HTTP_404_NOT_FOUND)
