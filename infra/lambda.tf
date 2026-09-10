resource "aws_cloudwatch_log_group" "ingest" {
  name              = "/aws/lambda/${var.project_name}-ingest"
  retention_in_days = 14
  tags              = local.common_tags
}

resource "aws_lambda_function" "ingest" {
  function_name = "${var.project_name}-ingest"
  role          = aws_iam_role.lambda.arn
  handler       = "src.ingest.handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 60
  memory_size   = 512
  tags          = local.common_tags

  filename         = "${path.module}/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda.zip")

  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.data.id
    }
  }

  depends_on = [aws_cloudwatch_log_group.ingest]
}