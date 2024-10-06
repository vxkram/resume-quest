import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class SummaryView(APIView):
    def get(self, request, file_name, *args, **kwargs):

        json_file_path = os.path.join('saved_jsons', f"{file_name}.json")  

        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                data = json.load(json_file)
                
                return Response({"summary": data.get("summary", "")}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Summary not found."}, status=status.HTTP_404_NOT_FOUND)
