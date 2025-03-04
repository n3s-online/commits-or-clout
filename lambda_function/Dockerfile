FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.9

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install the dependencies
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy function code and other necessary files
COPY src/ ${LAMBDA_TASK_ROOT}/
COPY favicons/ ${LAMBDA_TASK_ROOT}/favicons/

# Set the CMD to your handler (module.function_name format)
CMD ["lambda_handler.handler"] 