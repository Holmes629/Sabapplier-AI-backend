FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
    
# Copy project files
COPY . ${LAMBDA_TASK_ROOT}

# Command to run the Django app using Lambda
CMD [ "manage.lambda_handler" ]
