FROM public.ecr.aws/lambda/python:3.11

COPY app.py photo_info.py __init__.py requirements.txt ./

RUN yum update -y && \
   yum install -y mesa-libGL && \
   python3.11 -m pip install -r requirements.txt -t .

# Command can be overwritten by providing a different command in the template directly.
CMD ["app.lambda_handler"]