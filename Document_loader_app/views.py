import os.path
from pathlib import Path

from django.http import HttpResponse
from django.shortcuts import render
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser, FormParser

from .models import UploadedFile
from .serializers import UploadedFileSerializer
from langchain.document_loaders import JSONLoader
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, UnstructuredFileLoader, \
    UnstructuredImageLoader
import json
import docx2txt


class UploadedFileCreateAPIView(CreateAPIView):
    serializer_class = UploadedFileSerializer
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = UploadedFileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            uploaded_files = UploadedFile.objects.filter(id=serializer.data['id'])
            interact = uploaded_files.first()
            pdf_files = [interact.file.path]
            for file_path in pdf_files:
                file_name = os.path.basename(file_path)
                if file_name.endswith('.pdf'):
                    pdf_loader = PyPDFLoader(file_path)
                    documents = pdf_loader.load()
                    print(documents)
                elif file_name.endswith('.docx'):
                    word_loader = Docx2txtLoader(file_path)
                    documents = word_loader.load()
                    print(documents)
                elif file_name.endswith('.txt'):
                    txt_loader = TextLoader(file_path)
                    documents = txt_loader.load()
                    print(documents)
                elif file_name.endswith('.json'):
                    with open(file_path) as file:
                        documents = json.load(file)
                        print(documents)
                    # Rest of your code for processing the documents
                elif file_name.endswith('.jpg') or file_name.endswith('.png'):
                    img_loader = UnstructuredImageLoader(file_path, mode="elements")
                    documents = img_loader.load()
                    print(documents)
                else:
                    unstructured_loader = UnstructuredFileLoader(file_path)
                    documents = unstructured_loader.load()
                    print(documents)
                if file_name.endswith('.json'):
                    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
                    docs = text_splitter.create_documents(documents)
                else:
                    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
                    docs = text_splitter.split_documents(documents)

                embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                os.remove(file_path)
                db = FAISS.from_documents(docs, embeddings)
                db.save_local('index_store')
                return HttpResponse('Successfully loaded')
        else:
            return HttpResponse(serializer.errors)
